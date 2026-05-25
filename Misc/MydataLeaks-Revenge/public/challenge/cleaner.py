#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据清洗与脱敏脚本
存在多个已知缺陷，仅供内部测试使用
"""
import csv
import json
import hashlib
import re
import logging
import os
from pathlib import Path

# 确保在 challenge 目录下运行
os.chdir(Path(__file__).parent)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('retry.log'),
        logging.StreamHandler()
    ]
)

class DataCleaner:
    def __init__(self):
        self.data = []
        self.retry_cache = {}  # BUG: 重试缓存未正确清理

    def load_sys_a(self):
        """加载系统A数据"""
        try:
            with open('raw_sys_a.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.data.append({
                        'id': row['student_id'],
                        'name': row['name'],
                        'phone': row['phone'],
                        'email': row['email'],
                        'source': 'sys_a'
                    })
        except Exception as e:
            logging.error(f"加载 sys_a 失败: {e}")

    def load_sys_b(self):
        """加载系统B数据 - BUG: 编码处理错误"""
        try:
            # BUG: 先尝试 UTF-8，失败后降级到 GBK，但未正确处理
            with open('raw_sys_b.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.data.append({
                        'id': row['sid'],
                        'name': row['fullname'],
                        'idcard': row['idcard'],
                        'password': row['password'],
                        'source': 'sys_b'
                    })
        except UnicodeDecodeError:
            logging.warning("UTF-8 解码失败，降级到 GBK")
            with open('raw_sys_b.csv', 'r', encoding='gbk', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.data.append({
                        'id': row['sid'],
                        'name': row['fullname'],
                        'idcard': row['idcard'],
                        'password': row['password'],
                        'source': 'sys_b'
                    })

    def load_sys_c(self):
        """加载系统C数据"""
        try:
            with open('raw_sys_c.json', 'r', encoding='utf-8') as f:
                records = json.load(f)
                for row in records:
                    self.data.append({
                        'id': row['stu_id'],
                        'name': row['stu_name'],
                        'phone': row['contact'],
                        'idcard': row['id_number'],
                        'source': 'sys_c'
                    })
        except Exception as e:
            logging.error(f"加载 sys_c 失败: {e}")

    def desensitize_name(self, name):
        """脱敏姓名 - BUG: 异常时返回缓存残留"""
        try:
            if not name or len(name) < 2:
                raise ValueError("Invalid name")
            return hashlib.sha1(name.encode()).hexdigest()
        except Exception as e:
            logging.warning(f"姓名脱敏失败: {name}, 使用缓存")
            return self.retry_cache.get('name', name)  # BUG: 返回上次失败的缓存

    def desensitize_phone(self, phone):
        """脱敏手机号"""
        if not phone or len(phone) != 11:
            return phone
        return phone[:3] + "****" + phone[-4:]

    def desensitize_idcard(self, idcard):
        """脱敏身份证 - BUG: 规则不一致"""
        if not idcard or len(idcard) < 10:
            return idcard
        # BUG: 有时用 keep_6_4，有时用 keep_4_4
        if len(idcard) == 18:
            return idcard[:6] + "********" + idcard[-4:]
        return idcard[:4] + "****" + idcard[-4:]

    def desensitize_password(self, pwd):
        """脱敏密码 - BUG: 已是 MD5 时不处理"""
        if re.match(r'^[a-f0-9]{32}$', pwd):
            return pwd  # 已经是 MD5
        return hashlib.md5(pwd.encode()).hexdigest()

    def process_record(self, record, batch_id, idx):
        """处理单条记录 - BUG: 异常重试时污染缓存"""
        try:
            cleaned = {
                'id': record['id'],
                'name': self.desensitize_name(record.get('name', '')),
                'phone': self.desensitize_phone(record.get('phone', '')),
                'idcard': self.desensitize_idcard(record.get('idcard', '')),
                'password': self.desensitize_password(record.get('password', 'default')),
                'email': record.get('email', '').split('@')[-1] if '@' in record.get('email', '') else '',
                'source': record['source']
            }
            return cleaned
        except Exception as e:
            logging.error(f"批次 {batch_id} 记录 {idx} 处理失败: {e}")
            # BUG: 失败时将部分数据写入缓存，影响下一条
            self.retry_cache = record
            return None

    def deduplicate(self):
        """去重 - BUG: 使用 name+phone 组合而非 id 作为主键"""
        seen = set()
        unique_data = []
        for record in self.data:
            # BUG: 应该用 id，但错误地用了 name+phone 组合
            key = record.get('name', '') + record.get('phone', '')
            if key not in seen:
                seen.add(key)
                unique_data.append(record)
        self.data = unique_data
        logging.info(f"去重后剩余 {len(self.data)} 条记录")

    def export(self, filename='cleaned_students.csv'):
        """导出清洗后的数据"""
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['id', 'name', 'phone', 'idcard', 'password', 'email', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.data)
        logging.info(f"导出完成: {filename}")

    def run(self):
        """执行清洗流程"""
        logging.info("开始数据清洗...")
        self.load_sys_a()
        self.load_sys_b()
        self.load_sys_c()

        logging.info(f"加载完成，共 {len(self.data)} 条原始记录")

        # 处理所有记录
        processed = []
        for i, record in enumerate(self.data):
            result = self.process_record(record, batch_id=i//100, idx=i)
            if result:
                processed.append(result)

        self.data = processed
        self.deduplicate()
        self.export()
        logging.info("清洗完成！")

if __name__ == '__main__':
    cleaner = DataCleaner()
    cleaner.run()
