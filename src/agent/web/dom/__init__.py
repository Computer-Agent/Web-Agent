from src.agent.web.dom.views import DOMElementNode, DOMState
from playwright.async_api import ElementHandle
from typing import TYPE_CHECKING
import asyncio

if TYPE_CHECKING:
    from src.agent.web.context import Context

class DOM:
    def __init__(self, context:'Context'):
        self.context=context

    async def get_state(self,use_vision:bool=False)->tuple[str|None,DOMState]:
        '''Get the state of the webpage.'''
        with open('./src/agent/web/dom/script.js') as f:
                script=f.read()
        # Loading the script
        await self.context.execute_script(script)
        # Get interactive elements
        await asyncio.sleep(2)
        nodes=await self.context.execute_script('getInteractiveElements()')
        # print(nodes)
        # Add bounding boxes to the interactive elements
        await self.context.execute_script('nodes=>{mark_page(nodes)}',nodes)
        if use_vision:
            screenshot=await self.context.get_screenshot(save_screenshot=False)
        else:
            screenshot=None
        # Remove bounding boxes
        await self.context.execute_script('unmark_page()')
        selector_map=await self.build_selector_map(nodes)
        return (screenshot,DOMState(nodes=list(selector_map.values()),selector_map=selector_map))


    async def build_selector_map(self, nodes: list[dict]) -> dict[int, tuple[DOMElementNode, ElementHandle]]:
        """Build a map from element index to node."""
        async def process_node(index: int, node: dict):
            handle = await self.context.execute_script(
                'index => getElementByIndex(index)', 
                index, 
                enable_handle=True
            )
            element_handle = handle.as_element()
            element_node = DOMElementNode(
                tag=node.get('tag'),
                role=node.get('role'),
                name=node.get('name'),
                attributes=node.get('attributes'),
                bounding_box=node.get('box')
            )
            return index, (element_node, element_handle)

        tasks = [process_node(index, node) for index, node in enumerate(nodes)]
        results = await asyncio.gather(*tasks)
        return dict(results)