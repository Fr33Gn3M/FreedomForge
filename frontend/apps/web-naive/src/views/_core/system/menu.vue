<script lang="ts" setup>
import type { MenuItem } from '#/api/core/system';
import type { VxeGridProps } from '#/adapter/vxe-table';

import { ref } from 'vue';

import { Page } from '@vben/common-ui';
import { useVbenModal } from '@vben-core/popup-ui';

import { NButton, NSelect, NSpace, NTag } from 'naive-ui';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  createMenuApi,
  deleteMenuApi,
  getMenuListApi,
  updateMenuApi,
} from '#/api/core/system';

// ====== Grid ======
const [Grid, gridApi] = useVbenVxeGrid({
  gridOptions: {
    columns: [
      { type: 'seq', width: 60, title: '#' },
      {
        field: 'name',
        title: '菜单名称',
        minWidth: 200,
        treeNode: true,
      },
      {
        field: 'type',
        title: '类型',
        width: 80,
        slots: { default: 'type' },
      },
      { field: 'path', title: '路由路径', minWidth: 160 },
      { field: 'permission_code', title: '权限码', minWidth: 160 },
      { field: 'sort', title: '排序', width: 60 },
      {
        field: 'status',
        title: '状态',
        width: 70,
        slots: { default: 'status' },
      },
      {
        field: 'action',
        title: '操作',
        width: 200,
        fixed: 'right',
        slots: { default: 'action' },
      },
    ],
    toolbarConfig: { buttons: [] },
    treeConfig: { transform: true, parentField: 'parent_id' },
    proxyConfig: {
      ajax: {
        query: async () => {
          const list = await getMenuListApi();
          return { items: list, total: list.length };
        },
      },
    },
  },
});

// ====== Type labels ======
const typeLabels: Record<string, string> = {
  dir: '目录',
  menu: '菜单',
  button: '按钮',
};
const typeOptions = [
  { label: '目录', value: 'dir' },
  { label: '菜单', value: 'menu' },
  { label: '按钮', value: 'button' },
];

// ====== Edit modal ======
const parentOptions = ref<{ label: string; value: number }[]>([]);
const editForm = ref({
  id: 0,
  parent_id: 0,
  name: '',
  path: '',
  component: '',
  icon: '',
  type: 'menu' as string,
  permission_code: '',
  sort: 0,
  status: 1,
});
const isEdit = ref(false);

const [FormModal, formModalApi] = useVbenModal({
  title: '新增菜单',
  onOpenChange: async (isOpen) => {
    if (isOpen) {
      const row = formModalApi.getData<Record<string, any>>();
      // Load parent options (only dirs and menus, exclude buttons)
      const menus = await getMenuListApi();
      parentOptions.value = [
        { label: '根目录', value: 0 },
        ...menus
          .filter((m) => m.type !== 'button')
          .map((m) => ({ label: `${m.name} (${m.path || '/'})`, value: m.id })),
      ];

      if (row?.id) {
        isEdit.value = true;
        editForm.value = {
          id: row.id,
          parent_id: row.parent_id,
          name: row.name,
          path: row.path || '',
          component: row.component || '',
          icon: row.icon || '',
          type: row.type,
          permission_code: row.permission_code || '',
          sort: row.sort,
          status: row.status,
        };
      } else {
        isEdit.value = false;
        editForm.value = {
          id: 0, parent_id: 0, name: '', path: '', component: '', icon: '',
          type: 'menu', permission_code: '', sort: 0, status: 1,
        };
      }
    }
  },
  onConfirm: async () => {
    const data = { ...editForm.value };
    if (isEdit.value) {
      await updateMenuApi(data.id, data);
    } else {
      await createMenuApi(data);
    }
    gridApi?.reload();
    formModalApi.close();
  },
});

function openAdd(parentId = 0) {
  editForm.value.parent_id = parentId;
  formModalApi.setData(null).open();
}
function openEdit(row: Record<string, any>) {
  formModalApi.setData(row).open();
}
async function handleDelete(row: Record<string, any>) {
  await deleteMenuApi(row.id);
  gridApi?.reload();
}
</script>

<template>
  <Page>
    <Grid>
      <template #toolbar-actions>
        <NSpace>
          <NButton type="primary" size="small" @click="openAdd(0)">新增菜单</NButton>
          <NButton size="small" @click="gridApi?.reload()">刷新</NButton>
        </NSpace>
      </template>

      <template #type="{ row }">
        <NTag :type="row.type === 'dir' ? 'info' : row.type === 'menu' ? 'success' : 'default'" size="small">
          {{ typeLabels[row.type] || row.type }}
        </NTag>
      </template>

      <template #status="{ row }">
        <NTag :type="row.status === 1 ? 'success' : 'default'" size="small">
          {{ row.status === 1 ? '启用' : '禁用' }}
        </NTag>
      </template>

      <template #action="{ row }">
        <NSpace>
          <NButton v-if="row.type !== 'button'" size="tiny" quaternary @click="openAdd(row.id)">
            新增子项
          </NButton>
          <NButton size="tiny" type="primary" quaternary @click="openEdit(row)">
            编辑
          </NButton>
          <NButton size="tiny" type="error" quaternary @click="handleDelete(row)">
            删除
          </NButton>
        </NSpace>
      </template>
    </Grid>

    <!-- Form Modal -->
    <FormModal>
      <div style="display:flex;flex-direction:column;gap:14px;padding:8px 0;max-height:60vh;overflow-y:auto">
        <div>
          <label>上级菜单</label>
          <select v-model="editForm.parent_id" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px">
            <option v-for="p in parentOptions" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
        </div>
        <div>
          <label>菜单名称 *</label>
          <input v-model="editForm.name" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px" placeholder="如：用户管理" />
        </div>
        <div>
          <label>菜单类型</label>
          <select v-model="editForm.type" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px">
            <option v-for="t in typeOptions" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>
        <div v-if="editForm.type !== 'button'">
          <label>路由路径</label>
          <input v-model="editForm.path" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px" placeholder="如：/system/user" />
        </div>
        <div v-if="editForm.type === 'menu'">
          <label>组件路径</label>
          <input v-model="editForm.component" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px" placeholder="如：/system/user/index" />
        </div>
        <div v-if="editForm.type !== 'button'">
          <label>图标</label>
          <input v-model="editForm.icon" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px" placeholder="如：icon-user" />
        </div>
        <div v-if="editForm.type === 'button'">
          <label>权限码</label>
          <input v-model="editForm.permission_code" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px" placeholder="如：system:user:add" />
        </div>
        <div>
          <label>排序</label>
          <input v-model.number="editForm.sort" type="number" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px" />
        </div>
        <div>
          <label>状态</label>
          <select v-model.number="editForm.status" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px">
            <option :value="1">启用</option>
            <option :value="0">禁用</option>
          </select>
        </div>
      </div>
    </FormModal>
  </Page>
</template>
