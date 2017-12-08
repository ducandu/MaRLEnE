"""
 -------------------------------------------------------------------------
 engine2learn - envs/openai_gym_env
 
 A proxy wrapper Env class for openAI gym-type envs.
  
 created: 2017/12/06 in PyCharm
 (c) 2017 Sven - ducandu GmbH
 -------------------------------------------------------------------------
"""

from .proxy_env import ProxyEnv


class OpenAIGymEnv(ProxyEnv):
    def __init__(self):
