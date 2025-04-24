__author__ = 'DucHung'
# -*- coding: utf-8 -*-

import configparser
from scrapy import settings
from datetime import datetime
from datetime import timedelta
import dateutil.parser
import time
import mysql.connector
import os
from .helper import Helper
class DispatcherLibrary:
    def __init__(self, service_id=None,group=None, *args, **kwargs):
        extra_config = configparser.ConfigParser()
        extra_config.read(settings.get('EXTRA_CONFIG_FILE'))
        self.extra_config = extra_config

        self.process_id = os.getpid()
        self.group_page = group
        self.service_id = service_id
        self.limit = 100
        self.DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def mysqConnect(self):
        self.conn = mysql.connector.connect(user=self.extra_config.get('mysql','db_username'),
                                    passwd=self.extra_config.get('mysql','db_password'),
                                    db=self.extra_config.get('mysql','db_name'),
                                    host=self.extra_config.get('mysql','db_host'),
                                    charset="utf8", use_unicode=True)
        self.cursor = self.conn.cursor()


    def mysqlQuery(self, sql, params=()):
        try:
            self.mysqConnect()
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            self.conn.commit()
        except (AttributeError, mysql.connector.OperationalError) as e:
            print ('exception generated during sql connection: ', e)
            self.mysqConnect()
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
        return cursor

    def spider_open(self):
        # print self.service_id
        print("test")
        if (self.service_id != None):
            current_time = time.time()
            sql1 = """SELECT id, process_id FROM crawl_manager_service_job WHERE service_id = %s AND status = 0 AND group_page = %s AND server_version = %s ORDER BY id DESC LIMIT 1"""
            process_info = self.mysqlQuery(sql1,(self.service_id, self.group_page, Helper().getServerVersion()))
            print(process_info)
            list_data = process_info.fetchone()
            if(list_data):
                sql = """DELETE FROM crawl_manager_service_job WHERE id = %s"""
                self.mysqlQuery(sql,(list_data[0],))
                command_str = 'kill -9 ' + list_data[1]
                os.system(command_str)
            now = datetime.now().strftime(self.DATETIME_FORMAT)

            sql = """INSERT INTO crawl_manager_service_job(service_id, process_id, status, start_time, group_page, server_version, starttime_string) VALUE (%s, %s, %s, %s, %s, %s,%s)"""
            curr = self.mysqlQuery(sql,(self.service_id, self.process_id, 0, current_time, self.group_page, Helper().getServerVersion(),now))

    def spider_close(self, reason):
        if (self.service_id != None):
            current_time = time.time()
            now = datetime.now().strftime(self.DATETIME_FORMAT)
            
            sql = """UPDATE crawl_manager_service_job SET `status` = %s, `finish_time` = %s, `finish_reason` = %s, `finishtime_string` = %s WHERE `service_id` = %s AND `process_id` = %s"""
            curr = self.mysqlQuery(sql,(1,current_time,reason, now, self.service_id, self.process_id))

    def getUrlLeech(self, domain, group, page):
        start = (page - 1) * self.limit
        sql = """SELECT id, domain_url, category_name, domain_name, domain_group, status, created, pay_category FROM web_url WHERE domain_name = %s AND domain_group = %s AND status = 1 ORDER BY id DESC LIMIT %s,%s"""
        curr = self.mysqlQuery(sql,(domain, group, start,self.limit))
        if curr :
            return curr.fetchall()
        else:
            return []

    def getDomainUrls(self, status):
        sql = """SELECT id, domain, url, xpath, xpath_children, status, created FROM web_category_xpath WHERE  status = %s """
        curr = self.mysqlQuery(sql % status)
        if curr :
            return curr.fetchall()
        else:
            return []

    def getCateUrls(self, domain):
        print(domain)
        sql = """SELECT id, domain_url, category_name, domain_name, domain_group, status, created, pay_category FROM web_url WHERE domain_name = '%s' AND  status = active AND domain_group != 'HGR1' ORDER BY RAND()"""
        curr = self.mysqlQuery(sql % domain)
        print(curr.fetchall())
        if curr :
            return curr.fetchall()
        else:
            return []


    def getUrlLeechByGroup(self, group, page):
        start = (page - 1) * self.limit
        sql = """SELECT id, domain_url, category_name, domain_name, domain_group, status, created, pay_position_1, pay_position_2, pay_position_3, pay_position_4, pay_position_5, pay_position_6 FROM web_url WHERE domain_group = %s AND status = 1 ORDER BY id DESC LIMIT %s,%s"""
        curr = self.mysqlQuery(sql,(group, start,self.limit))
        if curr :
            return curr.fetchall()
        else:
            return []

    def insertErrorLink(self, web_link, web_domain, web_category_name, web_domain_group, web_domain_id):
        current_time = time.time()
        sql = """INSERT INTO web_crawled_error(web_link, web_domain, web_category_name, web_domain_group, web_domain_id, created) VALUE (%s, %s, %s, %s, %s, %s)"""
        curr = self.mysqlQuery(sql,(web_link, web_domain, web_category_name, web_domain_group, web_domain_id, current_time))