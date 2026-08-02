const XLSX = require('xlsx');
const path = require('path');
const fs = require('fs');

const dir = 'C:/Users/11039/Desktop/文档资料/国元证券/智能门户功能清单（更新至V2.4.0）';

const files = [
    "会议管家(增购).xlsx",
    "待办中心(增购).xlsx",
    "快捷表单(增购).xlsx",
    "新闻公告(增购).xlsx",
    "日程中心(增购).xlsx",
    "统一搜索线点平台(增购).xlsx",
    "自定义门户(增购).xlsx",
    "门户管理后台(基础).xlsx",
    "集成中心RC平台(增购).xlsx",
];

for (const f of files) {
    console.log('\n' + '='.repeat(80));
    console.log('FILE: ' + f);
    console.log('='.repeat(80));
    try {
        const wb = XLSX.readFile(path.join(dir, f));
        console.log('Sheets: ' + wb.SheetNames.join(', '));
        for (const sn of wb.SheetNames) {
            const ws = wb.Sheets[sn];
            const data = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });
            console.log('\n--- Sheet: ' + sn + ' (rows: ' + data.length + ') ---');
            for (const row of data) {
                console.log(row.map(c => String(c).trim()).join(' | '));
            }
        }
    } catch (e) {
        console.log('Error: ' + e.message);
    }
}
