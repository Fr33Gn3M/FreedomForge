<script lang="ts" setup>

import type { MenuItem } from '#/api/core/system';

import { ref } from 'vue';

import { Page, useVbenModal } from '@vben/common-ui';

import { NButton, NSpace, NTag, NTree } from 'naive-ui';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  createRoleApi,
  deleteRoleApi,
  getMenuListApi,
  getRoleListApi,
  getRoleMenuIdsApi,
  setRoleMenusApi,
  updateRoleApi,
} from '#/api/core/system';

// ====== Grid ======
const [Grid, gridApi] = useVbenVxeGrid({
  gridOptions: {
    columns: [
      { type: 'seq', width: 60, title: '#' },
      { field: 'name', title: '角色名称', minWidth: 120 },
      { field: 'code', title: '角色编码', width: 100 },
      { field: 'description', title: '描述', minWidth: 180 },
      {
        field: 'status',
        title: '状态',
        width: 80,
        slots: { default: 'status' },
      },
      {
        field: 'action',
        title: '操作',
        width: 240,
        fixed: 'right',
        slots: { default: 'action' },
      },
    ],
    toolbarConfig: { buttons: [] },
    proxyConfig: {
      ajax: {
        query: async () => {
          const res = await getRoleListApi();
          return { items: res.list, total: res.total };
        },
      },
    },
  },
});

// ====== Add/Edit modal ======
const editForm = ref({ id: 0, name: '', code: '', description: '' });
const isEdit = ref(false);

const [FormModal, formModalApi] = useVbenModal({
  title: '新增角色',
  onOpenChange: async (isOpen) => {
    if (isOpen) {
      const row = formModalApi.getData<Record<string, any>>();
      if (row?.id) {
        isEdit.value = true;
        editForm.value = {
          id: row.id,
          name: row.name,
          code: row.code,
          description: row.description || '',
        };
      } else {
        isEdit.value = false;
        editForm.value = { id: 0, name: '', code: '', description: '' };
      }
    }
  },
  onConfirm: async () => {
    await (isEdit.value
      ? updateRoleApi(editForm.value.id, {
          name: editForm.value.name,
          description: editForm.value.description,
        })
      : createRoleApi({
          name: editForm.value.name,
          code: editForm.value.code,
          description: editForm.value.description,
        }));
    gridApi?.reload();
    formModalApi.close();
  },
});

function openAdd() {
  formModalApi.setData(null).open();
}
function openEdit(row: Record<string, any>) {
  formModalApi.setData(row).open();
}

// ====== Permission modal ======
const permRoleId = ref(0);
const permRoleName = ref('');
const allMenus = ref<MenuItem[]>([]);
const checkedMenuIds = ref<number[]>([]);

const [PermModal, permModalApi] = useVbenModal({
  title: '分配权限',
  onOpenChange: async (isOpen) => {
    if (isOpen) {
      const row = permModalApi.getData<Record<string, any>>();
      permRoleId.value = row.id;
      permRoleName.value = row.name;
      const [menus, ids] = await Promise.all([
        getMenuListApi(),
        getRoleMenuIdsApi(row.id),
      ]);
      allMenus.value = menus;
      checkedMenuIds.value = ids;
    }
  },
  onConfirm: async () => {
    await setRoleMenusApi(permRoleId.value, checkedMenuIds.value);
    gridApi?.reload();
    permModalApi.close();
  },
});

function openPerm(row: Record<string, any>) {
  permModalApi.setData(row).open();
}

async function handleDelete(row: Record<string, any>) {
  await deleteRoleApi(row.id);
  gridApi?.reload();
}

// ====== Tree helpers ======
function buildTree(menus: MenuItem[], parentId = 0): any[] {
  return menus
    .filter((m) => m.parent_id === parentId)
    .map((m) => ({
      key: m.id,
      label: `${m.name}${m.permission_code ? ` (${m.permission_code})` : ''}`,
      children: buildTree(menus, m.id),
    }));
}
</script>

<template>
  <Page>
    <Grid>
      <template #toolbar-actions>
        <NSpace>
          <NButton type="primary" size="small" @click="openAdd">
新增角色
</NButton>
          <NButton size="small" @click="gridApi?.reload()">刷新</NButton>
        </NSpace>
      </template>

      <template #status="{ row }">
        <NTag :type="row.status === 1 ? 'success' : 'default'" size="small">
          {{ row.status === 1 ? '启用' : '禁用' }}
        </NTag>
      </template>

      <template #action="{ row }">
        <NSpace>
          <NButton size="tiny" type="primary" quaternary @click="openPerm(row)">
权限
</NButton>
          <NButton size="tiny" quaternary @click="openEdit(row)">编辑</NButton>
          <NButton
            size="tiny"
            type="error"
            quaternary
            :disabled="row.code === 'super'"
            @click="handleDelete(row)"
          >
            删除
          </NButton>
        </NSpace>
      </template>
    </Grid>

    <!-- Add/Edit Modal -->
    <FormModal>
      <div
        style="display: flex; flex-direction: column; gap: 16px; padding: 8px 0"
      >
        <div>
          <label>角色名称</label>
          <input
            v-model="editForm.name"
            style="
              width: 100%;
              padding: 8px;
              border: 1px solid #d9d9d9;
              border-radius: 4px;
            "
            placeholder="如：财务主管"
          />
        </div>
        <div>
          <label>角色编码</label>
          <input
            v-model="editForm.code"
            :disabled="isEdit"
            style="
              width: 100%;
              padding: 8px;
              border: 1px solid #d9d9d9;
              border-radius: 4px;
            "
            placeholder="如：finance_admin"
          />
        </div>
        <div>
          <label>描述</label>
          <input
            v-model="editForm.description"
            style="
              width: 100%;
              padding: 8px;
              border: 1px solid #d9d9d9;
              border-radius: 4px;
            "
          />
        </div>
      </div>
    </FormModal>

    <!-- Permission Modal -->
    <PermModal>
      <div style="padding: 8px 0">
        <p style="margin-bottom: 12px; font-weight: 600">
          为「{{ permRoleName }}」分配菜单权限：
        </p>
        <NTree
          :data="buildTree(allMenus, 0)"
          :checked-keys="checkedMenuIds"
          checkable
          cascade
          block-node
          default-expand-all
          @update:checked-keys="(keys: number[]) => (checkedMenuIds = keys)"
        />
      </div>
    </PermModal>
  </Page>
</template>
