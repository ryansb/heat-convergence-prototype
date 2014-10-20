import logging

from .framework import datastore

from . import resource
from . import template


logger = logging.getLogger('stack')

stacks = datastore.Datastore('Stack',
                             'key', 'name', 'tmpl_key')


class Stack(object):
    def __init__(self, name, tmpl, key=None):
        self.key = key
        self.tmpl = tmpl
        self.data = {
            'name': name,
            'tmpl_key': tmpl.key,
        }

    def __str__(self):
        return '<Stack %r>' % self.key

    @classmethod
    def load(cls, key):
        s = stacks.read(key)
        return cls(s.name, template.Template.load(s.tmpl_key),
                   key=s.key)

    def store(self):
        if self.key is None:
            self.key = stacks.create(**self.data)
        else:
            stacks.update(self.key, **self.data)

    def create(self):
        self.store()

        logger.info('[%s(%d)] Created' % (self.data['name'], self.key))

        resources = {name: resource.Resource(name, self, defn)
                         for name, defn in self.tmpl.resources.items()}

        deps = self.tmpl.dependencies()
        logger.debug('[%s(%d)] Dependencies: %s' % (self.data['name'],
                                                    self.key, deps.graph()))

        for rsrc_name in deps:
            resources[rsrc_name].store()

        from . import processes
        for rsrc_name in deps.leaves():
            processes.converger.check_resource(resources[rsrc_name].key)