import type { RouteRecordStringComponent } from '@vben/types';

import { requestClient } from '#/api/request';

/**
 * 获取当前用户可访问的菜单树（从 Python 后端 /menu/all）
 */
export async function getAllMenusApi() {
  try {
    return requestClient.get<RouteRecordStringComponent[]>('/menu/all');
  } catch {
    return [] as RouteRecordStringComponent[];
  }
}
