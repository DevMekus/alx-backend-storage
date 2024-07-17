#!/usr/bin/env python3
'''module for using the Redis
'''
import uuid
import redis
from functools import wraps
from typing import Any, Callable, Union


def count_calls(method: Callable) -> Callable:
    '''Function Tracks the number of calls made
    '''
    @wraps(method)
    def invoker(self, *args, **kwargs) -> Any:
        '''Function Invokes the given method 
        '''
        if isinstance(self._redis, redis.Redis):
            self._redis.incr(method.__qualname__)
        return method(self, *args, **kwargs)
    return invoker


def call_history(method: Callable) -> Callable:
    '''Function Tracks the call details of a method 
    '''
    @wraps(method)
    def invoker(self, *args, **kwargs) -> Any:
        '''Function Returns the method's output after storing 
        '''
        inkey = '{}:inputs'.format(method.__qualname__)
        outkey = '{}:outputs'.format(method.__qualname__)
        if isinstance(self._redis, redis.Redis):
            self._redis.rpush(inkey, str(args))
        output = method(self, *args, **kwargs)
        if isinstance(self._redis, redis.Redis):
            self._redis.rpush(outkey, output)
        return output
    return invoker


def replay(fn: Callable) -> None:
    '''Function Displays the call history of a Cache 
    '''
    if fn is None or not hasattr(fn, '__self__'):
        return
    redisStore = getattr(fn.__self__, '_redis', None)
    if not isinstance(redisStore, redis.Redis):
        return
    fxNme = fn.__qualname__
    in_key = '{}:inputs'.format(fxNme)
    out_key = '{}:outputs'.format(fxNme)
    fxn_call_count = 0
    if redisStore.exists(fxNme) != 0:
        fxn_call_count = int(redisStore.get(fxNme))
    print('{} was called {} times:'.format(fxNme, fxn_call_count))
    fxn_inputs = redisStore.lrange(in_key, 0, -1)
    fxn_outputs = redisStore.lrange(out_key, 0, -1)
    for fxn_input, fxn_output in zip(fxn_inputs, fxn_outputs):
        print('{}(*{}) -> {}'.format(
            fxNme,
            fxn_input.decode("utf-8"),
            fxn_output,
        ))


class Cache:
    '''Function Represents an object for storing data
    '''
    def __init__(self) -> None:
        '''Initializes a Cache instance.
        '''
        self._redis = redis.Redis()
        self._redis.flushdb(True)

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        '''Function Stores a value in a Redis data storage 
        '''
        dataKey = str(uuid.uuid4())
        self._redis.set(dataKey, data)
        return dataKey

    def get(
            self,
            key: str,
            fn: Callable = None,
            ) -> Union[str, bytes, int, float]:
        '''Function Retrieves a value from a Redis data storage.
        '''
        data = self._redis.get(key)
        return fn(data) if fn is not None else data

    def get_str(self, key: str) -> str:
        '''Function Retrieves a string value from a Redis data storage.
        '''
        return self.get(key, lambda x: x.decode('utf-8'))

    def get_int(self, key: str) -> int:
        '''Function Retrieves an integer value from a Redis data storage.
        '''
        return self.get(key, lambda x: int(x))
