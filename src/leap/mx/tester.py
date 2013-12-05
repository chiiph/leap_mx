import argparse
import ConfigParser
import sys
import os
import datetime

from twisted.internet import reactor, defer
from twisted.python import filepath, log

from leap.mx import couchdbhelper
from leap.mx.mail_receiver import MailReceiver
from leap.soledad.common.document import SoledadDocument

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LEAP MX tester script')
    parser.add_argument('--process-mail', nargs="?",
                        metavar="/path/to/email",
                        dest="mail",
                        help=("Email to process"))
    parser.add_argument('--produce-dummy-mail', nargs="?",
                        metavar="UUID",
                        dest="uuid",
                        help=(
                            "Directly save a dummy email to Soledad. To get "
                            "the uuid for a user, you might want to run "
                            "postmap -v -q <email address> tcp:localhost:4242"))

    args = parser.parse_args()
    if not ((args.mail is not None) ^ (args.uuid is not None)):
        print "ERROR: Can only set one option"
        parser.print_help()
        quit()

    log.startLogging(sys.stdout)

    log.msg("Starting test for %s..." % (fullpath,))

    config_file = "/etc/leap/mx.conf"

    config = ConfigParser.ConfigParser()
    config.read(config_file)

    user = config.get("couchdb", "user")
    password = config.get("couchdb", "password")

    server = config.get("couchdb", "server")
    port = config.get("couchdb", "port")

    cdb = couchdbhelper.ConnectedCouchDB(server,
                                         port=port,
                                         dbName="identities",
                                         username=user,
                                         password=password)

    # Mail receiver
    mail_couch_url_prefix = "http://%s:%s@%s:%s" % (user,
                                                    password,
                                                    server,
                                                    port)

    mr = MailReceiver(mail_couch_url_prefix, cdb, [])

    if args.mail is not None:
        fullpath = os.path.realpath(args.mail)
        fpath = filepath.FilePath(fullpath)

        d = mr._process_incoming_email(None, fpath, 0)
        d.addCallback(lambda x: reactor.stop())
    elif args.uuid is not None:
        doc = SoledadDocument(doc_id=str(pyuuid.uuid4()))

        message = """
From: LEAP MX Tester <noreply@bitmask.net>
To: Unknown User <noreply-user@bitmask.net>
Subject: Test dummy mail (%s)

This is an automatically generated dummy email to test connectivity
between mails saved in Soledad from the LEAP MX daemon.

If you receive this, be happy, things are working!
        """ % (datetime.datetime.now(),)
        data = {'incoming': True, 'content': message}

        d = mr._export_message(args.uuid, doc)
        d.addCallback(lambda x: reactor.stop())
    else:
        print "Nothing to do here..."
        quit()

    reactor.run()
