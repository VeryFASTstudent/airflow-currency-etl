// Capture actual Docker-hosted web interfaces during CI. Never capture .env.
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    const mongo = await browser.newContext({viewport:{width:1440,height:1000},httpCredentials:{username:process.env.ME_USERNAME,password:process.env.ME_PASSWORD}});
    const page = await mongo.newPage();
    await page.goto('http://127.0.0.1:8081/', {waitUntil:'networkidle'});
    const database = page.getByRole('link', {name:'currency_etl',exact:true});
    if (await database.count()) await database.click();
    const collection = page.getByRole('link',{name:'exchange_rates',exact:true});
    if (await collection.count()) await collection.click();
    await page.screenshot({path:'evidence/06_mongo_express_ui.png',fullPage:true});
    const airflow = await browser.newPage({viewport:{width:1440,height:1000}});
    await airflow.goto('http://127.0.0.1:8080/', {waitUntil:'networkidle'});
    const username = airflow.locator('input[name="username"], input[id="username"]');
    if (await username.count()) {
      await username.first().fill('admin');
      await airflow.locator('input[type="password"]').first().fill('admin');
      await airflow.locator('button[type="submit"], input[type="submit"]').first().click();
      await airflow.waitForLoadState('networkidle');
    }
    const dag = airflow.getByRole('link',{name:'currency_exchange_etl',exact:true});
    if (await dag.count()) await dag.first().click();
    await airflow.screenshot({path:'evidence/07_airflow_ui.png',fullPage:true});
  } finally { await browser.close(); }
})().catch(e => {console.error(e.message);process.exit(1);});
