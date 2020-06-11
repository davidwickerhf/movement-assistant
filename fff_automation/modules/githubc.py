from github import Github
import re
from fff_automation.modules import settings

USER = settings.get_var('GIT_USER')
TOKEN = settings.get_var('GIT_TOKEN')
# either github username of name of organisation hosting the git repository
git_name = settings.get_var('GIT_NAME')
git_repo = settings.get_var('GIT_REPO')
g = Github(TOKEN)

ISSUE, FEATURE_REQUEST, FEEDBACK, QUESTION = range(4)
ACTIVATE, ALL_GROUPS, ARCHIVE_GROUP, UNARCHIVE_GROUP, DELETE_GROUP, NEW_CALL, ALL_CALLS, DELETE_CALL, TRUST_USER, OTHER = range(
    10)

label_keys = {
    ISSUE: 'Issue',
    FEATURE_REQUEST: 'Feature Request',
    FEEDBACK: 'Feedback',
    QUESTION: 'Question',
}

issue_types = {
    ACTIVATE: '/activate',
    ALL_GROUPS: '/groups',
    ARCHIVE_GROUP: '/archive',
    UNARCHIVE_GROUP: '/unarchive',
    DELETE_GROUP: '/deletegroup',
    NEW_CALL: '/newcall',
    ALL_CALLS: '/calls',
    DELETE_CALL: '/deletecall',
    TRUST_USER: '/trust',
    OTHER: 'Other'
}


def create_issue(feedback):
    print('GITHUBC: create_issue()')
    g_labels = []
    repo = g.get_repo("{}/{}".format(git_name, git_repo))

    # ADD ISSUE
    issue = repo.create_issue(
        title=feedback.title, body=feedback.body, labels=g_labels)
    # ADD LABELS
    issue.add_to_labels(repo.get_label('Code Feedback'))
    issue.add_to_labels(repo.get_label(label_keys.get(feedback.get_type())))
    issue.add_to_assignees(USER)

    feedback.id = issue.id
    feedback.json = issue.url
    url = issue.url
    url = re.sub('api.', '', url)
    url = re.sub('repos/', '', url)
    feedback.url = url
    return feedback
