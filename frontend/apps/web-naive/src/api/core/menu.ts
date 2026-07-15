import type { RouteRecordStringComponent } from '@vben/types';

import { requestClient } from '#/api/request';

/**
 * 获取用户所有菜单（Python 后端暂未实现，返回空数组）
 */
export async function getAllMenusApi() {
  try {
    return requestClient.get<RouteRecordStringComponent[]>('/menu/all');
  } catch {
    // Python 后端暂未实现，返回空菜单列表
    return [] as RouteRecordStringComponent[];
  }
}
