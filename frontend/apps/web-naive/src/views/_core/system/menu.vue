<script lang="ts" setup>

import { ref } from 'vue';

import { Page, useVbenModal } from '@vben/common-ui';

import { NButton, NInput, NSelect, NSpace, NTag } from 'naive-ui';

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
          id: 0,
          parent_id: 0,
          name: '',
          path: '',
          component: '',
          icon: '',
          type: 'menu',
          permission_code: '',
          sort: 0,
          status: 1,
        };
      }
    }
  },
  onConfirm: async () => {
    const data = { ...editForm.value };
    await (isEdit.value ? updateMenuApi(data.id, data) : createMenuApi(data));
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
        <NTag
          :type="
            row.type === 'dir'
              ? 'info'
              : row.type === 'menu'
                ? 'success'
                : 'default'
          "
          size="small"
        >
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
          <NButton
            v-if="row.type !== 'button'"
            size="tiny"
            quaternary
            @click="openAdd(row.id)"
          >
            新增子项
          </NButton>
          <NButton size="tiny" type="primary" quaternary @click="openEdit(row)">
            编辑
          </NButton>
          <NButton
            size="tiny"
            type="error"
            quaternary
            @click="handleDelete(row)"
          >
            删除
          </NButton>
        </NSpace>
      </template>
    </Grid>

    <!-- Form Modal -->
    <FormModal>
      <div style="display: flex; flex-direction: column; gap: 14px; max-height: 60vh; padding: 8px 0; overflow-y: auto">
        <div>
          <label style="display: block; margin-bottom: 4px">上级菜单</label>
          <NSelect v-model:value="editForm.parent_id" :options="parentOptions" placeholder="选择上级菜单" />
        </div>
        <div>
          <label style="display: block; margin-bottom: 4px">菜单名称 *</label>
          <NInput v-model:value="editForm.name" placeholder="如：用户管理" />
        </div>
        <div>
          <label style="display: block; margin-bottom: 4px">菜单类型</label>
          <NSelect v-model:value="editForm.type" :options="typeOptions" placeholder="选择类型" />
        </div>
        <div v-if="editForm.type !== 'button'">
          <label style="display: block; margin-bottom: 4px">路由路径</label>
          <NInput v-model:value="editForm.path" placeholder="如：/system/user" />
        </div>
        <div v-if="editForm.type === 'menu'">
          <label style="display: block; margin-bottom: 4px">组件路径</label>
          <NInput v-model:value="editForm.component" placeholder="如：/system/user/index" />
        </div>
        <div v-if="editForm.type !== 'button'">
          <label style="display: block; margin-bottom: 4px">图标</label>
          <NInput v-model:value="editForm.icon" placeholder="如：lucide:user" />
        </div>
        <div v-if="editForm.type === 'button'">
          <label style="display: block; margin-bottom: 4px">权限码</label>
          <NInput v-model:value="editForm.permission_code" placeholder="如：system:user:add" />
        </div>
        <div>
          <label style="display: block; margin-bottom: 4px">排序</label>
          <NInput v-model:value="editForm.sort" placeholder="0" />
        </div>
        <div>
          <label style="display: block; margin-bottom: 4px">状态</label>
          <NSelect v-model:value="editForm.status" :options="[{ label: '启用', value: 1 }, { label: '禁用', value: 0 }]" />
        </div>
      </div>
    </FormModal>
  </Page>
</template>
