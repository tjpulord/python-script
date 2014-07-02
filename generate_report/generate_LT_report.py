#/nb/python/bin/python

import csv
from datetime import datetime
import os
from optparse import OptionParser as OPs
import pgdb
import yaml
import sys

# If could not import excel r/w lib, we save it as plain text
excel_lib = True
try:
    import xlwt
    import xlrd
    import xlutils.copy as xlcopy
except:
    excel_lib = False


def parseConfig(config_file):
    try:
        fp = open(config_file)
        content = yaml.load(fp)
        fp.close()
    except Exception, e:
        print "Load config file: %s Failed" % config_file
        raise e
    return content

class MondbData(object):
    def __init__(self, hostname, database, user):
        self.hostname = hostname
        self.database = database
        self.user = user
    def connect(self):
        self.conn = pgdb.connect(host=self.hostname, database=self.database, user=self.user)
        self.cursor = self.conn.cursor()

    def get(self, sql):
        try:
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except pgdb.DatabaseError, e:
            print 'Error: %s' % e
            self.conn.rollback()
            return []
    def close(self):
        self.cursor.close()
        self.conn.close()

def parseOption():
    parse = OPs(usage='%prog [options] [NAME] [...]',\
                prog = '/nb/python/bin/python generate_LT_report.py')

    parse.add_option('-s', '--start_time', dest='start_time',
                     help='set the start time of the load test', default=None)
    parse.add_option('-e', '--end_time', dest='end_time',
                     help='set the end time of the load test', default=None)
    parse.add_option('-n', '--wokers', dest='num_worker',
                     help='input the number of the users/workers', default=None)
    parse.add_option('-a', '--slaves', dest='num_slave',
                     help='input the number of the slaves', default=None)
    parse.add_option('-c', '--csv_file', dest='csv_file',
                     help='save the report as csv file', default=None)
    parse.add_option('-x', '--excel_file', dest='excel_file',
                     help='save the report as excel file', default = None)
    parse.add_option('-l', '--html_file', dest='html_file',
                     help='save the report as html file', default = None)
    parse.add_option('-f', '--config', dest='config',
                     help='set the config file, or get from default path',
                     default=None)

    return parse


def write_excel_file(conf, param, excel_file):
    print 'write_excel_file ...'
    work_book = xlwt.Workbook()
    work_sheet = work_book.add_sheet('loading test report')
    row=0
    column = 0
    for res in fetch_data(conf, param):
        column=0
        for data in res:
            work_sheet.write(row, column, data)
            row += 1
            column += 1
    work_book.save(os.path.join(os.getcwd(), excel_file))

def write_html_file(conf, param, htmlfile):
    print 'write html file ...'
    suffix = '.html'
    try:
        if htmlfile.endswith('/'):
            htmlfile += conf['stime'] + suffix
        elif not htmlfile.endswith(suffix):
            htmlfile += suffix
        if htmlfile.startswith('/'):
            hfile = open(htmlfile, 'w')
        else:
            hfile = open(os.path.join(os.getcwd(), htmlfile), 'w')
    except Exception, e:
        print 'Could not open file %s' % htmlfile
        print 'Error', e
        return

    # write html head
    head = '<html><header><title>Loading Test Report</title></header><body>'
    hfile.writelines(head)
    # write content tables
    tables = '<table border="1">'
    for res in fetch_data(conf, param):
        if len(res) == 1 and res[0] == '\n':
            tables += '</table><br>\n'
            hfile.writelines(tables)
            tables = '<table border="1">'
        else:
            tables += '<tr><td>'+'</td><td>'.join(res) + '</td></tr>'
    tables += '</table>'
    hfile.writelines(tables)
    # write html footer and close html file
    footer = '</body></html>'
    hfile.writelines(footer)
    hfile.close()

def write_csv_file(conf, param, csvfile):
    print 'write csv file ...'
    # generate the csv file
    suffix = '.csv'
    try:
        cf = os.path.join(os.getcwd(), csvfile)
        writer = csv.writer(file(cf, 'wb'))
    except Exception, e:
        print 'Error %s' % e
        return

    for res in fetch_data(conf, param):
        writer.writerow(res)

def fetch_data(conf, param):
       
    def passorfail():
        plist = pair.get('pair')['data']
        a = float(plist[1] % content_dict)
        b = float(plist[2])
        if a < b:
            return 'Pass'
        else:
            return 'Fail'
    def formula_delta():
        plist = pair.get('pair')['data']
        res = float(plist[2]) - float(plist[1] % content_dict)
        return str('%.3f' % res)
    def formula_ratio():
        plist = pair.get('pair')['data']
        a = float(plist[1]%content_dict)
        b = float(plist[2])
        return str('%3.0f' % (a*100.0/b))+'%'
    def pct_total():
        plist = pair.get('pair')['data']
        try:
            num = float(plist[3]%content_dict)
        except:
            return None
        if total:
            return str('%0.0f'%(num*100.0/total)) + '%'
        else:
            return None
    def formula_pct():
        plist = pair.get('pair')['data']
        try:
            num = float(plist[1]%content_dict)
        except:
            return None
        if total:
            return str('%0.1f'%(num*100.0/total)) + '%'
        else:
            return None
    def pct_delta():
        plist = pair.get('pair')['data']
        num = 0
        try:
            num = float(plist[1]%content_dict)
        except Exception, e:
            print 'could not find the value of %s, error: %s' % (plist[1], e)
        if total:
            target = plist[3]
            ftarget = target.endswith('%%') and float(target.rpartition('%%')[0])
            return str('%.2f' % (ftarget-num*100.0/total)) + '%'
        else:
            return None
    def get_static():
        plist = pair.get('pair')['data']
        country = plist[0]%content_dict
        return pair.get('pair').get('static_data', {}).get(country)

    # output the summary part
    for k, v in conf.get('summary', {}).items():
        #print k, v % param
        yield [k, v%param]

    # output the file content
    pdb = MondbData('127.0.0.1', 'mon', 'monrpt')
    pdb.connect()
    file_content = conf.get('file_content')
    for item in file_content:
        yield ['\n',]
        yield item['title']
        if 'subtitle' in item:
            yield item['subtitle']
        #print '\t'.join(item['title'])
        total = None
        if 'total' in item:
            total = pdb.get(conf['sql'].get(item['total'])%param)
            if total:
                total = total[0][0]
        for pair in item['content-list']:
            sqlstr = pair.get('pair', {}).get('sql')
            if not sqlstr:
                yield [l%locals() for l in pair.get('pair')['data']]
                continue

            param.update(pair.get('pair').get('param', {}))
            print '*** sql: %s' % conf['sql'].get(sqlstr) % param
            mondbdata = pdb.get(conf['sql'].get(sqlstr) % param)
            print '/**** mondbdata %s ***/' % mondbdata
            for n, line in enumerate(mondbdata):
                content_dict = {}
                if len(line) > 1:
                    for i, v in enumerate(line):
                        content_dict['{}_{}'.format(sqlstr, i)] = str(v)
                elif line:
                    content_dict[sqlstr] = str(line[0])
                for formula in item.get('formulas',[]):
                    content_dict[formula] = locals()[formula]()
                yield [l%content_dict for l in pair.get('pair')['data'] ]
    pdb.close()


def main():

    # parse the option
    parse = parseOption()
    option, gs = parse.parse_args()
    # process the start/end time
    if not option.start_time or not option.end_time:
        print 'You should input the start time and end time.\n', parse.print_help()
        sys.exit()
    para_dict = {'stime': option.start_time, 'etime': option.end_time,
                 'num_worker': option.num_worker, 'num_slave': option.num_slave}
    timeformat = '%m/%d/%Y %H:%M'
    stime = datetime.strptime(option.start_time, timeformat)
    etime = datetime.strptime(option.end_time, timeformat)
    delta_time = etime - stime
    para_dict['duration'] = '{}:{}'.format(delta_time.seconds/3600, delta_time.seconds/60)
    para_dict['day_suffix'] = '_{}'.format(datetime.strftime(stime, '%d'))
    # parse the config file.
    if option.config:
        conf = parseConfig(option.config)
    else:
        current_config = os.path.join(os.getcwd(), 'sql.conf')
        if os.path.exists(current_config):
            conf = parseConfig(current_config)
        else:
            print 'Could not find the config file. exit'
            sys.exit()
    # write to file
    if option.csv_file:
        write_csv_file(conf, para_dict, option.csv_file)
    elif option.excel_file:
        write_excel_file(conf, para_dict, option.excel_file)
    elif option.html_file:
        write_html_file(conf, para_dict, option.html_file)
    else:
        print 'should set the output file name.\n', parse.print_help()

if __name__ == '__main__':
    print 'generate report'
    main()

    # pdb = MondbData('127.0.0.1', 'mon', 'monrpt')
    # pdb.connect()
    # sql = "select module_name, avg(tps) from (select module_name, date_trunc('second', time), count(*) as tps from tps_servlet_reply_events_04 where module_name in ('mobius_nav') and time > '2014-06-04 23:10:00' and time < '2014-06-04 23:59:59' group by 1, 2) as times group by 1;"
    # data = pdb.get(sql)
    # print 'data', data
    # pdb.close()
