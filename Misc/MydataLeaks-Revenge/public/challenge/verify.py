import csv

data = list(csv.DictReader(open('cleaned_students.csv', encoding='utf-8')))

# 年份分布
years = {}
for r in data:
    y = r['id'][:4]
    years[y] = years.get(y, 0) + 1

print('年份分布:')
for y in sorted(years.keys()):
    print(f'  {y}: {years[y]} 条 ({years[y]/len(data)*100:.1f}%)')

# 检查原始数据中的姓名
print('\n原始数据姓名样例:')
raw_a = list(csv.DictReader(open('raw_sys_a.csv', encoding='utf-8')))
for i in range(10):
    print(f'  {raw_a[i]["name"]}')
