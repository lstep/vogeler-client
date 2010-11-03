# -*- coding: utf-8 -*-
# vim:syntax=python:sw=4:ts=4:expandtab
#

from vogelerclient import __version__ as version
from amqplib import client_0_8 as amqp
import urlparse,logging,sys,platform,shlex,subprocess
import socket

# Configure Logs
log = logging.getLogger('vogeler-client')

# Correct problem with urlparse in python < 2.6
SCHEME="amqp"
urlparse.uses_netloc.append(SCHEME)
urlparse.uses_fragment.append(SCHEME)

try:
    import simplejson as json
except ImportError:
    import json

class Manager(object):
    def __init__(self,config):
        self.config = config
        self.ch = None
        self.master_exchange = config.get('main', 'master_exchange')
        #self.queue = self.config.get('main', 'server_queue')
        if config.has_option('main','local_node_name'):
            self.local_node_name = config.get('main','local_node_name')
        else:
            self.local_node_name = socket.getfqdn(platform.node())

        self.setup_amqp_client()

    def setup_amqp(self):
        dsn = self.config.get('main', 'amqpserver')
        parsed = urlparse.urlparse(dsn)
        u,p,h,pt,vh = (parsed.username, parsed.password, parsed.hostname,
                       parsed.port, parsed.path)

        log.debug('Will connect to AMQP server at %s', dsn)
        try:
            conn = amqp.Connection(host="%s:%d" % (h,pt),
                                   userid=u, password=p,
                                   virtual_host=vh,
                                   ssl=self.config.getboolean('main','use_amqp_ssl'),
                                   insist=False)

            ch = conn.channel()
            ch.access_request(vh,active=True, read=True, write=True)
        except Exception,e:
            log.fatal('Unable to connect to amqp: %s' % e)
            sys.exit(1)

        return ch


    def setup_amqp_client(self):
        """ Setup a client AMQP binding """
        broadcast_exchange = self.config.get('main','broadcast_exchange')
        node_name = client_queue = self.local_node_name
        self.queue = self.local_node_name

        ch = self.setup_amqp()

        try:
            # define our incoming and outgoing queues
            log.debug('Declaring a queue named %s' % node_name)
            ch.queue_declare(node_name, durable=True, auto_delete=False)
            # bind our queues to the channel
            # this is for broadcast messages from the Vogeler server
            log.debug('Bind queue %s to bcast exchg %s with routing key=%s' % (node_name,broadcast_exchange,'broadcasts.*'))
            ch.queue_bind(client_queue, broadcast_exchange, routing_key='broadcasts.*')
            # this is for messages intended for us over the same topic exchange
            log.debug('Bind queue %s to bcast exchg %s with routing key=%s' % (node_name,broadcast_exchange,node_name))
            ch.queue_bind(client_queue, broadcast_exchange, routing_key=node_name)
        except Exception,e:
            log.fatal('Unable to setup amqp channels: %s' % e)
            sys.exit(1)

        self.ch = ch

    def message(self, message, durable=True):
        exchange = self.master_exchange
        try:
            log.debug("Vogeler is sending a message")
            msg = amqp.Message(json.dumps(message))
            if durable:
                msg.properties['delivery_mode'] = 2
            self.ch.basic_publish(msg, exchange=exchange)
        except Exception,e:
            log.fatal("Could not publish message to the queue")

    def process_request(self,request):
        log.info("Received request for: %s" % request)
        # Run plugin HERE
        #
        if request.has_key('myrequest'):
            req = request['myrequest']
            if self.config.has_section(req):
                command = self.config.get(req,'command')
                plugin_format = self.config.get(req,'format')
                message = subprocess.Popen(shlex.split(command), stdout = subprocess.PIPE).communicate()

                results = {'syskey': self.local_node_name, 'message': message[0], 'format': plugin_format}
                self.message(results)
                log.debug('Results: %s' % results)
            else:
                log.error("Expected presence of plugin %s, but not found in config file" % req)

        else:
            log.error("Wrong message format, was waiting for key 'myrequest':%s" % request)



    def callback(self, msg):
        log.debug('Message received')
        try:
            message = json.loads(msg.body)
        except Exception,e:
            log.warn("Message not in JSON format")
        self.process_request(message)

    def monitor(self):
        log.debug('Waiting for message(s) in queue %s' % self.queue)
        self.ch.basic_consume(self.queue,
                              callback=self.callback,
                              no_ack=True)
        while self.ch.callbacks:
            self.ch.wait()


def main(config,infos,args):
    print "vogelerclient version",version

    m = Manager(config)
    m.monitor()
