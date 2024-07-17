#!/usr/bin/env python3
'''A module with tools for request caching and tracking.
'''
import redis
import requests
from functools import wraps
from typing import Callable


redis_store = redis.Redis()
'''module-level 
'''


def data_cacher(method: Callable) -> Callable:
    '''Function Caches the output of fetched data.
    '''
    @wraps(method)
    def invoker(url) -> str:
        '''The function The wrapper function for caching the output.
        '''
        redisstore.incr(f'count:{url}')
        result = redisstore.get(f'result:{url}')
        if result:
            return result.decode('utf-8')
        result = method(url)
        redisstore.set(f'count:{url}', 0)
        redisstore.setex(f'result:{url}', 10, result)
        return result
    return invoker


@data_cacher
def get_page(url: str) -> str:
    '''Returns the content of a URL after caching the request's response,
    and tracking the request.
    '''
    return requests.get(url).text
