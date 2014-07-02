from tesla import std, env
from tesla import instances, netclient
from tesla.tps import tpselt
from tesla.servlet.tps.getattr import *
from datetime import datetime
import threading
import time
from optparse import OptionParser
from select import select
import sys
import profile
import hotshot

try:
    import pgdb
except ImportError:
    import psycopg2 as pgdb


######################### DEFAULT CLIENT SECTION #############################

## abnav_gen
#MDN = '9999999476'
#TPSLIB = env.tstest.tpslib

## vnav
MDN = '9999999012'
TPSLIB = env.system_test_tpslibs.vnav_client.filename

sms_thread = None
## default route through the tmcs:
## 107P04358,107P04359,107P04360,107P12898,107N13905,107N13904,107N13903,107N13902
#ROUTE = '41.643226,-87.507026,41.65966,-87.516868'

## default route through the tmcs:
## 120P11331,120N15723,120P15326,120P15300,120P15301,120N15318,120N16031,120P06744,
## 120P06746,120P06747,120N07063,120N07062,120N07061,120N07060,120P06971
ROUTE = '40.75397,-73.966058,40.755791,-73.952454'

## number of notify queries
NUM_UPDATES = 500

## period between traffic notify queries sent (in seconds)
TN_QUERY_PERIOD = 15

## delay between nav and first notify queries
STARTUP_DELAY = 0

## listening for SMS
SMS_CHECK = False

## send TN query after getting an SMS
CLIENT_EMULATION = False

## Print out queries and responces content
DEBUG = False

##############################################################################


def debug(*args):
    # to be replaced with actual logger if requested
    pass


def info(str, start_time=None, fmt='%Y-%m-%d %H:%M:%S.%f', nobr=False):
    now = datetime.now()
    if nobr:
        print '\r',
    if start_time:
        delta = now - start_time
        print "[{}]({:.2f}) {}".format(now.strftime(fmt), delta.total_seconds(), str),
    else:
        print "[{}] {}".format(now.strftime(fmt), str),
    if not nobr:
        print
    else:
        sys.stdout.flush()


def make_client():
    libset = instances.tps_libset()
    tl = libset.openuser(tpslib)
    iden = env.tstest.iden
    iden['attrs']['mdn'] = ['uint', mdn]
    client = netclient.TeslaClient(env.tstest.muxhost, env.tstest.muxport, iden, tl)
    return client


def query(e, servlet):
    client = std.autopromise(make_client)
    return client.tps_query(servlet, e, exsource=servlet)


def nav_query(route):
    sexp = """
        (nav-query (pronun-style female-1-qcp command-set-version e language en-GB)
          (want-traffic-notification)
          (route-style (vehicle-type car optimize fastest)
            (avoid (value toll)))
          (origin ()
            (point (lat [double]{} lon [double]{})))
          (destination ()
            (point (lat [double]{} lon [double]{})))
          (cache-contents ()
            (cache-item (name NIM0))
            (cache-item (name NIM1))
            (cache-item (name NIM2))
            (cache-item (name NIM3))
            (cache-item (name NIM4))
            (cache-item (name NIM5))
            (cache-item (name NIM6))
            (cache-item (name NIM7))))""".format(*route)
    debug(sexp)
    tps_query = tpselt.fromsexp(sexp)
    reply = query(tps_query, "nav,usa")
    debug(reply.tosexp())
    return reply


def notify_query(tri):
    sexp = """
        (traffic-notify-query ()
          (traffic-record-identifier (value "{}")
            (nav-progress
              (session-id "{}"
                position [uint]19863
                state START
                route-id |Vjo/wpo+LkTDlsKkQTHDvwdEC3g=|))))""".format(tri, tri)
    debug(sexp)
    global tps_query
    tps_query = tpselt.fromsexp(sexp)
    profiler = hotshot.Profile("test_hotshot.prof")
    profiler.run("reply = query(tps_query, 'traffic-notify,usa')")
    #reply = query(tps_query, 'traffic-notify,usa')
    #profile.run("reply = query(tps_query, 'traffic-notify,usa')")
    debug(reply.tosexp())
    return reply

mondb = {
  'user': 'monrpt',
  'password': 'markers',
  'host': 'mondb',
  'database': 'mon'
}

dbconn = pgdb.connect(**mondb)
cursor = dbconn.cursor()
sqlquery = """
            SELECT smpp.ctime AS ctime
            FROM smpp_proxy_events AS smpp, nav_reply_events AS nav
            WHERE nav.mdn='%s' AND nav.ctime > '%s' AND
            smpp.destination = nav.mdn AND smpp.ctime >= nav.ctime
            GROUP BY smpp.ctime
           """


def parseCommandLine(args):
    usage = "usage: %prog [options]"
    description = "Send nav/notify request"
    version = "TNS check tool 0.1"
    parser = OptionParser(usage=usage,
        version=version, description=description)
    parser.add_option("-r", "--route", action="store", metavar="route",
                      help="specify route points", type="string", dest="route",
                      default=ROUTE)
    parser.add_option("-t", "--tmc-list", action="store_true",
                      help="print out tmc list for the route", dest="print_tmc_list",
                      default=False)
    parser.add_option("-m", "--mdn", action="store", metavar="mdn",
                      help="specify destination mdn", type="string", dest="mdn",
                      default=MDN)
    parser.add_option("-p", "--product", action="store", metavar="product",
                      help="specify product name", type="string", dest="product",
                      default=None)
    parser.add_option("-l", "--product-list", action="store_true",
                      help="print out available products", dest="print_product_list",
                      default=False)
    parser.add_option("-w", "--wait", action="store", metavar="startup_delay",
                      help="startup delay", type="int", dest="startup_delay",
                      default=STARTUP_DELAY)
    parser.add_option("-n", "--number", action="store", metavar="num_updates",
                      help="TN queries number", type="int", dest="num_updates",
                      default=NUM_UPDATES)
    parser.add_option("-i", "--interval", action="store", metavar="query_period",
                      help="TN query interval", type="int", dest="query_period",
                      default=TN_QUERY_PERIOD)
    parser.add_option("-s", "--sms-check", action="store_true",
                      help="check for SMS", dest="sms_check", default=SMS_CHECK)
    parser.add_option("-c", "--client-emulation", action="store_true",
                      help="send TN query after getting SMS", dest="client_emulation",
                      default=CLIENT_EMULATION)
    parser.add_option("-e", "--ensure-tmc-present", action="store",
                      metavar="ensure_tmc_present", type="string",
                      help="ensure that tmc is present in route",
                      dest="ensure_tmc_present", default=None)
    parser.add_option("-g", "--give-incident-delay",
                      action="store_true", dest="give_incident_delay",
                      help="give-back-incident-occurrence-delay",
                      default=False)
    parser.add_option("-f", "--ensure-tmc-flow-present", action="store",
                      metavar="ensure_tmc_flow_present", type="string",
                      help="ensure that tmc with flow is present in route",
                      dest="ensure_tmc_flow_present", default=None)
    parser.add_option("-d", "--debug", action="store_true",
                      help="print out queries", dest="debug", default=DEBUG)
    (options, args) = parser.parse_args(args)
    return options


def debug_func(turn_on):
    def debug_on(*args):
        args = '\n'.join('  >> ' + arg for arg in args)
        print(args)

    def debug_off(*args):
        pass

    return debug_on if turn_on else debug_off

SMS_caught = False

def start_sms_catching_thread():
    global sms_thread
    sms_thread = threading.Thread(target=sms_catching)
    sms_thread.daemon = True
    sms_thread.start()

def sms_catching():
    global SMS_caught
    posted_sms_prev = set()
    while 1:
        cursor.execute(sqlquery % (mdn, start_time.strftime('%Y-%m-%d %H:%M:%S.%f')))
        posted_sms_curr = cursor.fetchall()
        if posted_sms_curr:
            posted_sms_curr = set([x[0] for x in posted_sms_curr])
            posted_sms = posted_sms_curr - posted_sms_prev
            posted_sms_prev = posted_sms_curr
            if posted_sms:
                print
                info('OUTGOING SMS <== |\/|', start_time)
                SMS_caught = True
        time.sleep(0.2)

def sleeping(timeout):
    global SMS_caught
    rlist, _, _ = select([sys.stdin], [], [], timeout)
    if rlist:
        sys.stdin.readline()
        SMS_caught = True

def awaiting_sms():
    while 1:
        sleeping(0.2)
        if SMS_caught:
            break

tr_age = {0: 'old', 1: 'new'}
tr_type = {0: 'historical', 1: 'realtime', 2: 'fake'}

def nav_processing(reply):
    for flw_el in reply.getmany('traffic-flow'):
        age = int(te_gattru(flw_el, 'age'))
        s_age = tr_age[age]
        _type = te_gattru(flw_el, 'type')
        s_type = tr_type[_type]
        print ' ', s_type if not _type else s_age, (age, s_age, _type, s_type)
        for flw in flw_el.getmany('traffic-flow-item'):
            tmc = te_gattrs(flw, 'location')
            color = te_gattrs(flw, 'color')
            speed = te_gattrd(flw, 'speed')
            ffs = te_gattrd(flw, 'free-flow-speed')
            print '  |flw|', tmc, speed, ffs, color

def notify_processing(tri, start_time, ensure_tmc_flow_present):
    global SMS_caught
    info("notify_query ==>", start_time)
    reply = notify_query(tri)
    SMS_caught = False
    info("notify_reply <==", start_time)
    tri_el = reply.getone('traffic-record-identifier')
    notify_report = {'time': datetime.now(), 'is_flow': False, 'is_inc': False}
    for flw_el in tri_el.getmany('traffic-flow'):
        age = int(te_gattru(flw_el, 'age'))
        s_age = tr_age[age]
        _type = te_gattru(flw_el, 'type')
        s_type = tr_type[_type]
        print ' ', s_type if not _type else s_age, (age, s_age, _type, s_type)
        for flw in flw_el.getmany('traffic-flow-item'):
            tmc = te_gattrs(flw, 'location')
            color = te_gattrs(flw, 'color')
            speed = te_gattrd(flw, 'speed')
            ffs = te_gattrd(flw, 'free-flow-speed')
            if ensure_tmc_flow_present:
                flw_tmc, flw_speed = ensure_tmc_flow_present.split(':')
                if tmc == flw_tmc and int(speed) in [int(flw_speed), int(flw_speed)+1]:
                    notify_report['is_flow'] = True
            print '  |flw|', tmc, speed, ffs, color
    for inc_el in tri_el.getmany('traffic-incidents'):
        notify_report['is_inc'] = True
        age = int(not te_gattru(inc_el, 'age'))
        s_age = tr_age[age]
        print ' ', s_age
        for inc in inc_el.getmany('place'):
            inc_name = te_gattrs(inc, 'name')
            inc_loc = inc.getone('location')
            inc_road = te_gattrs(inc_loc, 'name')
            inc_pnt = inc_loc.getone('point')
            lat, lon = te_gattrd(inc_pnt, 'lat'), te_gattrd(inc_pnt, 'lon')
            print "  |inc| '{}: {}' ({}, {})".format(inc_road, inc_name, lat, lon)
    return notify_report

def main(args=sys.argv[1:]):
    global debug, mdn, tpslib, start_time
    options = parseCommandLine(args)
    debug = debug_func(options.debug)
    num_updates = options.num_updates
    query_period = options.query_period
    sms_check = options.sms_check
    route = options.route
    mdn = options.mdn
    product = options.product
    print_product_list = options.print_product_list
    print_tmc_list = options.print_tmc_list
    startup_delay = options.startup_delay
    client_emulation = options.client_emulation
    ensure_tmc_present = options.ensure_tmc_present
    ensure_tmc_flow_present = options.ensure_tmc_flow_present
    give_incident_delay = options.give_incident_delay
    if print_product_list:
        print "Product list:"
        print 'abnav_gen'
        for pr in env.system_test_tpslibs.keys():
            print pr
        sys.exit()
    if product:
        # using tpslib from system test
        if product == 'abnav_gen':
            tpslib = env.tstest.tpslib
        elif product in env.system_test_tpslibs:
            tpslib = env.system_test_tpslibs[product].filename
        else:
            print 'Product {} is not available'.format(product)
            print 'Use -l option to view product list \n' \
                  'or specify TPSLIB in DEFAULT CLIENT SECTION \n' \
                  'in the source'
            sys.exit()
    else:
        # using predefined tpslib from DEFAULT CLIENT SECTION
        tpslib = TPSLIB

    route = route.split(',')
    if len(route) != 4:
        print 'Wrong number of arguments'
        sys.exit()
    print 'origin: ({}, {})'.format(*route[0:2])
    print 'destination: ({}, {})'.format(*route[2:4])
    start_time = datetime.now()
    info("nav_query ==>", start_time)
    reply = nav_query(route)
    info("nav_reply <==", start_time)
    tmc_list = set()
    for nav_man in reply.getmany('nav-maneuver'):
        for tr_reg in nav_man.getmany('traffic-region'):
            tmc_list.add(te_gattrs(tr_reg, 'location'))
    if print_tmc_list:
        print 'tmcs under route:'
        for x in tmc_list:
            print ' ', x
    if ensure_tmc_present:
        if ensure_tmc_present not in tmc_list:
            print "TMC isn't presented in route"
            sys.exit()
    nav_processing(reply)
    tri_element = reply.getone('traffic-record-identifier')
    tri = te_gattrs(tri_element, 'value')
    print '  |tri|', tri
    if startup_delay:
        time.sleep(startup_delay)
    if sms_check:
        start_sms_catching_thread()
    for i in xrange(num_updates):
        notify_report = notify_processing(tri, start_time, ensure_tmc_flow_present)
        if ensure_tmc_flow_present and notify_report['is_flow']:
            print 'Flow is present'
            return notify_report['time']
        if give_incident_delay and notify_report['is_inc']:
            print 'Incident is present'
            return notify_report['time']
        if client_emulation:
            print "Waiting SMS or hit 'Enter' to send TN query"
            awaiting_sms()
            continue
        if i != num_updates - 1:
            print "Timeout {} sec or hit 'Enter' to send TN query"\
                .format(query_period)
            sleeping(query_period)


if __name__ == '__main__':
    try:
        main()
        print 'INFO: TN polling is done'
        while True:
            info('waiting...', start_time, nobr=True)
            sms_thread.join(1)
    except KeyboardInterrupt:
        print 'bye...'

