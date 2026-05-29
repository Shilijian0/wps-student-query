import os
import pandas as pd
from playwright.sync_api import sync_playwright

# 1. 配置路径（改用相对路径，方便开源与协作）
INPUT_EXCEL = "data/students.xlsx"  # 请在项目目录下创建 data 文件夹并放入你的学生表
OUTPUT_CSV = "output/查询结果.csv"

def run_query():
    # 检查输入文件是否存在
    if not os.path.exists(INPUT_EXCEL):
        print(f"错误: 未找到输入文件 '{INPUT_EXCEL}'，请检查路径。")
        return

    print("正在读取学生数据...")
    # 读取Excel/CSV数据，统一将关键列设为字符串，防止手机号或学号变形
    student_data = pd.read_excel(INPUT_EXCEL, dtype={"学生学号": str, "手机号": str})

    # 2. 启动 Playwright 执行自动化查询
    with sync_playwright() as p:
        print("正在启动 Edge 浏览器...")
        browser = p.chromium.launch(
            channel="msedge",
            headless=False,  # 设置为 True 可隐藏浏览器界面后台运行
            slow_mo=300      # 减慢操作速度，防止被网站识别为恶意攻击
        )
        page = browser.new_page()
        result_list = []

        total_students = len(student_data)
        for idx, row in student_data.iterrows():
            stu_id = str(row["学生学号"]).strip()
            stu_name = str(row["姓名"]).strip()
            stu_phone = str(row["手机号"]).strip()

            print(f"[{idx + 1}/{total_students}] 正在查询: {stu_name} (学号: {stu_id})...")

            try:
                # 打开查询页面
                page.goto("https://web.wps.cn/etapps/query/q/Y5oHzY3D")
                page.wait_for_load_state("domcontentloaded")

                # 3. 填充表单输入框
                page.fill('input[placeholder="请输入学号"]', stu_id)
                page.fill('input[placeholder="请输入姓名"]', stu_name)
                page.fill('input[placeholder="请输入手机号"]', stu_phone)

                # 4. 点击查询并等待结果
                page.click('button:has-text("查询")')
                # 等待特定结果元素加载（超时时间5秒）
                page.wait_for_selector('div[class*="item-title"]:has-text("新排名")', timeout=5000)

                # 5. 提取解析 DOM 节点数据
                rank = page.locator('div[class*="item-title"]:has-text("新排名") + div span[class*="text"]').text_content().strip()
                total_credit = page.locator('div[class*="item-title"]:has-text("总学分") + div span[class*="text"]').text_content().strip()
                weighted_score = page.locator('div[class*="item-title"]:has-text("加权平均分") + div span[class*="text"]').text_content().strip()

                result_list.append({
                    "学号": stu_id,
                    "姓名": stu_name,
                    "手机号": stu_phone,
                    "排名": rank,
                    "总学分": total_credit,
                    "加权平均分": weighted_score
                })

            except Exception as e:
                result_list.append({
                    "学号": stu_id,
                    "姓名": stu_name,
                    "手机号": stu_phone,
                    "排名": "查询失败",
                    "总学分": "查询失败",
                    "加权平均分": "查询失败"
                })
                print(f"⚠️ 学号 {stu_id} 查询异常: {str(e)}")

        # 6. 自动创建输出目录并保存结果
        os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
        pd.DataFrame(result_list).to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        browser.close()

    print(f"🎉 查询全部完成！结果已成功保存至: {OUTPUT_CSV}")

if __name__ == "__main__":
    run_query()
