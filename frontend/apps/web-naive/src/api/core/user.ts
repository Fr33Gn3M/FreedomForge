import type { UserInfo } from '@vben/types';

import { requestClient } from '#/api/request';

/** Python 后端 /users/me 返回的数据格式 */
interface PythonUserInfo {
  avatar: string;
  email: string;
  nickname: string;
  roles: string[];
  username: string;
}

/**
 * 获取用户信息 - 调用 Python 后端的 /users/me 接口
 * 将 Python 返回格式映射为 Vben UserInfo 类型
 */
export async function getUserInfoApi() {
  const data = await requestClient.get<PythonUserInfo>('/users/me');

  // 映射到 Vben UserInfo 格式
  return {
    avatar: data.avatar || '',
    desc: '',
    homePath: '/dashboard',
    realName: data.nickname || data.username,
    roles: data.roles || [],
    token: '',
    userId: data.username,
    username: data.username,
  } as UserInfo;
}
