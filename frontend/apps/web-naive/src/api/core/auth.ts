import { baseRequestClient, requestClient } from '#/api/request';

export namespace AuthApi {
  /** 登录接口参数 */
  export interface LoginParams {
    password?: string;
    username?: string;
  }

  /** 注册接口参数 */
  export interface RegisterParams {
    password?: string;
    username?: string;
    email?: string;
  }

  /** 登录接口返回值 */
  export interface LoginResult {
    accessToken: string;
  }

  export interface RefreshTokenResult {
    data: string;
    status: number;
  }
}

/**
 * 登录 - 调用 Python 后端的 /token 接口
 * Python 后端返回 {access_token, token_type}
 */
export async function loginApi(data: AuthApi.LoginParams) {
  const result = await requestClient.post<{
    access_token: string;
    token_type: string;
  }>('/token', data);

  // 映射 Python 后端字段到前端期望格式
  return { accessToken: result.access_token } as AuthApi.LoginResult;
}

/**
 * 注册 - 调用 Python 后端的 /register 接口
 */
export async function registerApi(data: AuthApi.RegisterParams) {
  return requestClient.post<{ username: string }>('/register', data);
}

/**
 * 刷新 accessToken（Python 后端暂未实现，保留接口）
 */
export async function refreshTokenApi() {
  return baseRequestClient.post<AuthApi.RefreshTokenResult>('/auth/refresh', {
    withCredentials: true,
  });
}

/**
 * 退出登录（调用 Python 后端的 /auth/logout 或忽略错误）
 */
export async function logoutApi() {
  try {
    return await baseRequestClient.post('/auth/logout', {
      withCredentials: true,
    });
  } catch {
    // 静默处理
    return;
  }
}

/**
 * 获取用户权限码
 */
export async function getAccessCodesApi() {
  try {
    const result = await requestClient.get<{ codes: string[] }>('/auth/codes');
    return result?.codes ?? [];
  } catch {
    return [] as string[];
  }
}
