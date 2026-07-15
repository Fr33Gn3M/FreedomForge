import { requestClient } from '#/api/request';

// ==================== 用户管理 ====================

export interface UserItem {
  id: number;
  username: string;
  email: string;
  nickname: string;
  avatar: string;
  role_id: number | null;
  role_code: string;
  role_name: string;
}

export interface UserListResult {
  total: number;
  list: UserItem[];
}

export async function getUserListApi(params: { page: number; page_size: number; keyword?: string }) {
  return requestClient.get<UserListResult>('/system/user/list', { params });
}

export async function updateUserApi(userId: number, data: { email?: string; nickname?: string; role_id?: number | null }) {
  return requestClient.put(`/system/user/${userId}`, data);
}

export async function deleteUserApi(userId: number) {
  return requestClient.delete(`/system/user/${userId}`);
}

// ==================== 角色管理 ====================

export interface RoleItem {
  id: number;
  name: string;
  code: string;
  description: string;
  status: number;
  created_at: string;
}

export interface RoleListResult {
  total: number;
  list: RoleItem[];
}

export async function getRoleListApi() {
  return requestClient.get<RoleListResult>('/system/role/list');
}

export async function getAllRolesApi() {
  return requestClient.get<RoleItem[]>('/system/role/all');
}

export async function createRoleApi(data: { name: string; code: string; description?: string }) {
  return requestClient.post('/system/role', data);
}

export async function updateRoleApi(roleId: number, data: Record<string, any>) {
  return requestClient.put(`/system/role/${roleId}`, data);
}

export async function deleteRoleApi(roleId: number) {
  return requestClient.delete(`/system/role/${roleId}`);
}

export async function getRoleMenuIdsApi(roleId: number) {
  return requestClient.get<number[]>(`/system/role/${roleId}/menus`);
}

export async function setRoleMenusApi(roleId: number, menuIds: number[]) {
  return requestClient.put(`/system/role/${roleId}/menus`, { menu_ids: menuIds });
}

// ==================== 菜单管理 ====================

export interface MenuItem {
  id: number;
  parent_id: number;
  name: string;
  path: string;
  component: string;
  icon: string;
  type: string;          // dir | menu | button
  permission_code: string;
  sort: number;
  status: number;
  created_at: string;
}

export async function getMenuListApi() {
  return requestClient.get<MenuItem[]>('/system/menu/list');
}

export async function createMenuApi(data: Partial<MenuItem>) {
  return requestClient.post('/system/menu', data);
}

export async function updateMenuApi(menuId: number, data: Partial<MenuItem>) {
  return requestClient.put(`/system/menu/${menuId}`, data);
}

export async function deleteMenuApi(menuId: number) {
  return requestClient.delete(`/system/menu/${menuId}`);
}
