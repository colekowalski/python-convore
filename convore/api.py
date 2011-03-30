# -*- coding: utf-8 -*-
"""
    convore.api
    ~~~~~~~~~~~

    This module implements the Convore API wrapper objects.

    :copyright: (c) 2011 by Kenneth Reitz.
    :license: ISC, see LICENSE for more details.
"""

import requests
from convore.packages.anyjson import deserialize
from datetime import datetime
import groups


API_URL = 'https://convore.com/api/'
AUTH = None

# =======
# Helpers
# =======

def _safe_response(r, error=None):
    try:
        r.raise_for_status()
        return r
    except requests.HTTPError:
        if r.status_code == 401:
            raise LoginFailed
        else:
            raise APIError(error) if error else APIError


def get(*path, **kwargs):
    """
    Accepts optional error parameter, which will be passed in the event of a
    non-401 HTTP error.

    api.get('groups')
    api.get('groups', 'id')
    api.get('accounts', 'verify')
    """
    url =  '%s%s%s' % (API_URL, '/'.join(map(str, path)), '.json')
    params = kwargs.get('params', None)
    req = requests.get(url, params=params, auth=auth)
    error = kwargs.get('error', None)
    return _safe_response(req, error)


def post(params, *path):
    url =  '%s%s%s' % (API_URL, '/'.join(map(str, path)), '.json')
    r = requests.post(url, params=params, auth=auth)
    return _safe_response(r)


class LoginFailed(RuntimeError):
    """Login falied!"""


class APIError(RuntimeError):
    """There was a problem properly accessing the Convore API."""


def login(username, password):
    """Configured API Credentials"""
    global auth
    auth = (username, password)
    # print requests.auth_manager.__dict__


class User(object):
    """Convore User object."""
    def __init__(self):
        self.username = None
        self.url = None
        self.id = None
        self.img = None

    def import_from_api(self, d):
        """Constructs User from Deserialized API Response."""
        self.username = d.get('username', None)
        self.url = d.get('url', None)
        self.id = d.get('id', None)
        self.img = d.get('img', None)

    def __repr__(self):
        return '<user @%s>' % (self.username)


class Group(object):
    """Convore Group object."""
    def __init__(self):
        self.kind = None
        self.members_count = None
        self.name = None
        self.creator = None
        self.url = None
        self.slug = None
        self.date_latest_message = None
        self.date_created = None
        self.topics_count = None
        self.friends = None
        self.unread = None
        self.id = None
        self.joined = False

    def import_from_api(self, d):
        """Constructs Group from Deserialized API Response."""
        self.kind = d.get('kind', None)
        self.members_count = d.get('members_count', None)
        self.name = d.get('name', None)
        self.url = d.get('url', None)
        self.slug = d.get('slug', None)
        self.date_latest_message = datetime.utcfromtimestamp(d.get('date_latest_message', None))
        self.date_created = datetime.utcfromtimestamp(d.get('date_created', None))
        self.topics_count = d.get('topics_count', None)
        self.unread = d.get('unread', None)
        self.id = d.get('id', None)
        self.creator = User()
        self.creator.import_from_api(d.get('creator', None))

        self.friends = []
        if 'friend_list' in d:
            for friend in d.get('friend_list', None):
                _user = User()
                _user.import_from_api(friend)
                self.friends.append(_user)

    def members(self):
        return Groups.get_group_members(self.id)

    def online_members(self):
        return Groups.get_group_online_members(self.id)

    def topics(self):
        return Groups.get_group_topics(self.id)

    def __repr__(self):
        return '<group %s>' % (self.slug)


class Topic(object):
    """Convore topic object"""
    def __init__(self):
        self.id = None
        self.name = None
        self.slug = None
        self.url = None
        self.message_count = None
        self.unread = None
        self.date_created = None
        self.date_latest_message = None
        self.creator = None

    def import_from_api(self, data):
        self.id = data.get('id', None)
        self.name = data.get('name', None)
        self.slug = data.get('slug', None)
        self.url = data.get('url', None)
        self.message_count = data.get('message_count', None)
        self.unread = data.get('unread', None)
        self.date_created = datetime.utcfromtimestamp(data.get('date_created', None))
        self.date_latest_message = datetime.utcfromtimestamp(data.get('date_latest_message', None))
        self.creator = User()
        self.creator.import_from_api(data.get('creator', None))

    def messages(self):
        return Topics.get_messages(self.id)


class Message(object):
    """Convore message object"""
    def __init__(self):
        self.id = None
        self.message = None
        self.date_created = None
        self.user = None

    def import_from_api(self, data):
        self.id = data.get('id', None)
        self.message = data.get('message', None)
        self.date_created = datetime.utcfromtimestamp(data.get('date_created', None))
        self.user = User()
        self.user.import_from_api(data.get('user', None))


class Category(object):
    def __init__(self):
        self.groups_count = None
        self.slug = None
        self.name = None
        self.groups = None

    def __repr__(self):
        return '<category %s>' % (self.slug)

    def import_from_api(self, d):
        """Constructs Category from deserialized API Response."""
        self.groups_count = d.get('groups_count', None)
        self.slug = d.get('slug', None)
        self.name = d.get('name', None)


class Groups(object):
    """Convore groups API wrapper"""

    @classmethod
    def get_user_groups(self):
        """Get a list of the current user's groups"""
        groups = []
        response = get('groups')
        for _group in deserialize(response.content)['groups']:
            group = Group()
            group.import_from_api(_group)
            group.joined = True
            groups.append(group)
        return groups

    @classmethod
    def get_group(self, group_id):
        """Get detailed information about a specified group"""
        response = get('groups', group_id)
        _group = deserialize(response.content)['group']
        group = Group()
        group.import_from_api(_group)
        return group

    @classmethod
    def get_group_members(self, group_id):
        """Get a list of members in a specified group"""
        users = []
        response = get('groups', group_id, 'members')
        for member in deserialize(response.content)['members']:
            user = User()
            user.import_from_api(member.get('user'))
            users.append(user)
        return users

    @classmethod
    def get_group_online_members(self, group_id):
        """Get a list of online members in a specified group"""
        users = []
        response = get('groups', group_id, 'online')
        for online in deserialize(response.content)['online']:
            user = User()
            user.import_from_api(online)
            users.append(user)
        return users

    @classmethod
    def get_group_topics(self, group_id):
        """Get a list of topics within a specified group"""
        topics = []
        response = get('groups', group_id, 'topics')
        for _topic in deserialize(response.content)['topics']:
            topic = Topic()
            topic.import_from_api(_topic)
            topics.append(topic)
        return topics


class Topics(object):
    @classmethod
    def get_topic(self, topic_id):
        response = get('topics', topic_id)
        _topic = deserialize(response.content)['topic']
        topic = Topic()
        topic.import_from_api(_topic)
        return topic

    @classmethod
    def get_messages(self, topic_id):
        messages = []
        response = get('topics', topic_id, 'messages')
        for _message in deserialize(response.content)['messages']:
            message = Message()
            message.import_from_api(_message)
            messages.append(message)
        return messages


class Messages(object):
    pass


class Users(object):
    @classmethod
    def get_user(self, user_id):
        response = get('users', user_id)
        _user = deserialize(response.content)['user']
        user = User()
        user.import_from_api(_user)
        return user
