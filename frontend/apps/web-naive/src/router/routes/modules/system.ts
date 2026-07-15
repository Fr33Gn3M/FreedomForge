import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    name: 'SystemParent',
    path: '/system',
    meta: {
      title: '系统管理',
      icon: 'icon-settings',
      authority: ['super', 'admin'],
    },
    children: [
      {
        name: 'SystemUser',
        path: '/system/user',
        component: () => import('#/views/_core/system/user.vue'),
        meta: {
          title: '用户管理',
          authority: ['super', 'admin'],
        },
      },
      {
        name: 'SystemRole',
        path: '/system/role',
        component: () => import('#/views/_core/system/role.vue'),
        meta: {
          title: '角色管理',
          authority: ['super', 'admin'],
        },
      },
      {
        name: 'SystemMenu',
        path: '/system/menu',
        component: () => import('#/views/_core/system/menu.vue'),
        meta: {
          title: '菜单管理',
          authority: ['super'],
        },
      },
    ],
  },
];

export default routes;
