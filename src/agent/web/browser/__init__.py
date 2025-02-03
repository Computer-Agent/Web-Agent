from playwright.async_api import async_playwright,Browser as PlaywrightBrowser,Playwright
from src.agent.web.browser.config import BrowserConfig,BROWSER_ARGS,SECURITY_ARGS
import asyncio

class Browser:
    def __init__(self,config:BrowserConfig=None):
        self.playwright:Playwright = None
        self.config = config if config else BrowserConfig()
        self.playwright_browser:PlaywrightBrowser = None
        self.loop = asyncio.get_event_loop()

    async def __aenter__(self):
        await self.init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_browser()

    async def init_browser(self):
        self.playwright =await async_playwright().start()
        self.playwright_browser = await self.setup_browser(self.config.browser)
    
    async def get_playwright_browser(self)->PlaywrightBrowser:
        if self.playwright_browser is None:
            await self.init_browser()
        return self.playwright_browser

    async def setup_browser(self,browser:str)->PlaywrightBrowser:
        parameters={
            'headless':self.config.headless,
            'downloads_path':self.config.downloads_path,
            'slow_mo':self.config.slow_mo,
            'args':BROWSER_ARGS + SECURITY_ARGS
        }
        if self.config.wss_url is not None:
            if browser=='chrome':
                browser_instance=await self.playwright.chromium.connect(self.config.wss_url)
            elif browser=='firefox':
                browser_instance=await self.playwright.firefox.connect(self.config.wss_url)
            elif browser=='edge':
                browser_instance=await self.playwright.chromium.connect(self.config.wss_url)
            else:
                raise Exception('Invalid Browser Type')
        elif self.config.user_data_dir is not None:
            browser_instance=None
        elif self.config.browser_instance_path is not None:
            #Only for chromium
            parameters.update({'executable_path':self.config.browser_instance_path})
            browser_instance=await self.playwright.chromium.launch(**parameters)
        else:
            if browser=='chrome':
                browser_instance=await self.playwright.chromium.launch(channel='chrome',**parameters)
            elif browser=='firefox':
                browser_instance=await self.playwright.firefox.launch(**parameters)
            elif browser=='edge':
                browser_instance=await self.playwright.chromium.launch(channel='msedge',**parameters)
            else:
                raise Exception('Invalid Browser Type')
        return browser_instance
    
    async def close_browser(self):
        try:
            if self.playwright_browser:
                await self.playwright_browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print('Browser failed to close')
        finally:
            self.playwright=None
            self.playwright_browser=None