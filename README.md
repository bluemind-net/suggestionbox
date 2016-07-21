Hello, this is the [BlueMind Suggestion
Box](https://community.bluemind.net/suggestions/)!

### Concept

We used to be overwhelmed by feature requests in our issue tracker
(Jira). The Suggestion Box is our solution to this problem: encourge
our users to vote and comment to other users' issues in a dedicated
website rather than duplicating them over and over in Jira.

### Issue storage

The Suggestion Box is heavily coupled with Jira, and can be seen as a
Jira front-end to handle tickets in a specific "SB" project. This is
good enough for us, but we'll be glad to merge pull requests that will
abstract the back-end and enable to store suggestions in other issue
trackers, or just about any database.

### User management

Any user may view suggestions, but one needs to be authenticated with
Jira (actually Atlassian Crowd SSO) to vote or post. This is again
good enought for us, but could/should be decoupled.

### Usage

This is nowhere next to a ready-to-deploy solution. Plenty of things
will need to be adapted to prove useful in other contexts than ours:
the settings.py file is your starting point.

### License

This code is published under the terms if the GNU AFFERO GENERAL
PUBLIC LICENSE Version 3, see agpl-3.0.txt