#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from flask import Flask, render_template, request, session, make_response, redirect, url_for, g, flash, abort
from flask.ext.cache import Cache
from jira.client import JIRA
from datetime import datetime
import crowd
import settings
import logging
import feedparser
import dateutil.parser

def parse_format_datetime(value):
    return dateutil.parser.parse(value).strftime('%d/%m/%Y, %H:%M')


app = Flask(__name__, static_url_path="/{}/static".format(settings.CONTEXT))
cache = Cache(app,config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': '/home/suggestions/cache'})
loggingHandler = logging.FileHandler(settings.LOGFILE)
loggingHandler.setLevel(logging.INFO)
loggingHandler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(loggingHandler)
app.secret_key = settings.SECRET_KEY
app.jinja_env.filters['datetime'] = parse_format_datetime
cs = crowd.CrowdServer(*settings.CROWD_CONF, ssl_verify=False)
jira_write = JIRA(settings.JIRA_URL, {'verify': False}, basic_auth=settings.USER)
jira_read = JIRA(settings.JIRA_URL, {'verify': False}, basic_auth=settings.RO_USER)

project = jira_read.project('SB')


@app.before_request
def validate_sso():
    crowd_infos = None
    sso_token = request.cookies.get('crowd.token_key')
    if sso_token:
        crowd_infos = cs.validate_session(sso_token)
    if not crowd_infos:
        g.jira = jira_read
        return
    g.name = crowd_infos['user']['name']
    if 'bm-dev' not in session:
        session['bm-dev'] = True if u'bm-dev' in cs.get_groups(g.name) else False
    g.jira = JIRA(settings.JIRA_URL, {'headers': {'Cookie': 'crowd.token_key={}'.format(sso_token),
                                                  'X-Atlassian-Token': 'no-check',
                                                  'Content-Type': 'application/json',
                                                  'Cache-Control': 'no-cache'},
                                      'verify': False})


@app.context_processor
def inject_login_url():
    return {'login_url': "{}?redirect={}".format(settings.LOGIN_URL, url_for('index', _external=True))}


@cache.cached(timeout=300, key_prefix='activity_stream')
def get_activity_stream():
    feed = feedparser.parse(settings.FEED_URL)
    entries = []
    for entry in feed['entries']:
        if "Sub-task" in str(entry):
            continue
        title = entry['title']
        title = title.replace(settings.JIRA_URL, 
                              settings.SB_URL)
        title = title.replace('href="{}"'.format(entry['author_detail']['href']), '')
        entries.append({ 
            'title': title,
            'updated': entry['updated']})
    return entries


@app.route("/{}/".format(settings.CONTEXT))
def index():
    session['search'] = search = request.args.get("search", '')
    session['component'] = component = request.args.get("component", '')
    session['include_done'] = include_done = request.args.get("include_done", '')
    textquery = 'AND text ~ "{}"'.format(search) if search else ''
    componentquery = 'AND component = {}'.format(component) if component not in ('', 'my') else ''
    myquery = 'AND reporter = currentUser()' if component == 'my' else ''
    statusFilter = 'AND status not in ("Done", "Closed")'
    if include_done:
        statusFilter = ''
    suggestions = g.jira.search_issues(
        'project=SB AND type=Suggestion {} {} {} {} order by votes, summary'.format(textquery, statusFilter, componentquery, myquery))
    return render_template('index.html', 
                           suggestions=suggestions,
                           components=project.components,
                           frontpage=True,
                           feed=get_activity_stream())


@app.route("/{}/details/<key>".format(settings.CONTEXT), methods=['GET', 'POST'])
def details(key):
    if request.method == 'POST':
        if getattr(g, "name", None) is None:
            return redirect(url_for('index'))    
        if 'comment' in request.form and request.form['comment']:
            g.jira.add_comment(key, request.form['comment'])
            flash('Your comment has been added to the suggestion.', 'confirmation')
        if 'vote' in request.form:
            if request.form['vote'] == '1':
                g.jira.add_vote(key)
                flash('Your vote has been added to the suggestion.', 'confirmation')
            else:
                g.jira.remove_vote(key)
                flash('Your vote has been removed.', 'confirmation')
        if 'file' in request.files and request.files['file'].filename:
            attachment = request.files['file']
            g.jira.add_attachment(key, attachment, attachment.filename)
            flash('Your attachment has been added to the suggestion.', 'confirmation')
    suggestion = g.jira.issue(key)    
    if suggestion.fields.issuetype.name != u'Suggestion':
        abort(404)
    elements = suggestion.fields.attachment + suggestion.fields.comment.comments
    elements.sort(key=lambda(e): e.created, reverse=True)
    return render_template('details.html', 
                           suggestion=suggestion, 
                           elements=elements,
                           components=project.components,
                           showreporter=True)


@app.route("/{}/new".format(settings.CONTEXT), methods=['GET', 'POST'])
def new():
    if getattr(g, "name", None) is None or request.referrer is None or (request.referrer.find('?search='), request.referrer.find('/new')) == (-1, -1):
        return redirect(url_for('index'))
    if request.method == 'POST':
        components = [{"id": arg[10:]} for arg in request.form if arg.startswith('component-')]
        if not request.form['summary']:
            flash("Title is mandatory!", 'warning')
        elif len(components) == 0:
            flash("You must select at least one component!", 'warning')
        else:            
            suggdict = {'project': {'key': 'SB'},
                        'summary': request.form['summary'],
                        'description': request.form['description'],
                        'components': components,
                        'issuetype': {'name': 'Suggestion'},
                        'reporter': {'name': g.name}}
            if 'internal' in request.form:
                suggdict['security'] = {'name': u'visible for Reporter and Blue Mind'}
            suggestion = jira_write.create_issue(suggdict)
            flash('Thanks for your suggestion! You may now join attachments.', 'confirmation')
            return redirect(url_for('details', key=suggestion.key))
    return render_template('new.html', components=project.components, form=request.form)



if __name__ == "__main__":
    with app.app_context():
        cache.clear()
    app.run(debug=True, host='0.0.0.0', port=3338)
