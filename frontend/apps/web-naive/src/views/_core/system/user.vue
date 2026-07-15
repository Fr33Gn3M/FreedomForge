<script lang="ts" setup>
import { ref } from 'vue';

import { Page, useVbenModal } from '@vben/common-ui';

import { NButton, NInput, NSelect, NSpace, NTag } from 'naive-ui';

import { useVbenVxeGrid } from '#/adapter/vxe-table';
import {
  deleteUserApi,
  getAllRolesApi,
  getUserListApi,
  updateUserApi,
} from '#/api/core/system';

// ====== Grid config ======
const [Grid, gridApi] = useVbenVxeGrid({
  gridOptions: {
    columns: [
      { type: 'seq', width: 60, title: '#' },
      { field: 'username', title: '用户名', minWidth: 120 },
      { field: 'email', title: '邮箱', minWidth: 180 },
      { field: 'nickname', title: '昵称', minWidth: 100 },
      {
        field: 'role_name',
        title: '角色',
        width: 120,
        slots: { default: 'role_name' },
      },
      {
        field: 'action',
        title: '操作',
        width: 160,
        fixed: 'right',
        slots: { default: 'action' },
      },
    ],
    toolbarConfig: { buttons: [] },
    proxyConfig: {
      ajax: {
        query: async ({ page }: { page: { currentPage: number; pageSize: number } }) => {
          const res = await getUserListApi({ page: page.currentPage, page_size: page.pageSize });
          return { items: res.list, total: res.total };
        },
      },
    },
  },
});

// ====== Edit modal ======
const editForm = ref({ id: 0, nickname: '', email: '', role_id: null as null | number });
const roleOptions = ref<{ label: string; value: number }[]>([]);

const [Modal, modalApi] = useVbenModal({
  title: '编辑用户',
  onOpenChange: async (isOpen) => {
    if (isOpen) {
      const row = modalApi.getData<Record<string, any>>();
      editForm.value = { id: row.id, nickname: row.nickname || '', email: row.email || '', role_id: row.role_id || null };
      const roles = await getAllRolesApi();
      roleOptions.value = roles.map((r: any) => ({ label: r.name, value: r.id }));
    }
  },
  onConfirm: async () => {
    await updateUserApi(editForm.value.id, { nickname: editForm.value.nickname, email: editForm.value.email, role_id: editForm.value.role_id });
    gridApi?.reload();
    modalApi.close();
  },
});

function openEdit(row: Record<string, any>) {
  modalApi.setData(row).open();
}

async function handleDelete(row: Record<string, any>) {
  await deleteUserApi(row.id);
  gridApi?.reload();
}
</script>

<template>
  <Page>
    <Grid>
      <template #toolbar-actions>
        <NSpace>
          <NButton type="primary" size="small" @click="gridApi?.reload()">刷新</NButton>
        </NSpace>
      </template>

      <template #role_name="{ row }">
        <NTag :type="row.role_code === 'super' ? 'error' : row.role_code === 'admin' ? 'warning' : 'info'" size="small">
          {{ row.role_name }}
        </NTag>
      </template>

      <template #action="{ row }">
        <NSpace>
          <NButton size="tiny" type="primary" quaternary @click="openEdit(row)">编辑</NButton>
          <NButton size="tiny" type="error" quaternary :disabled="row.role_code === 'super'" @click="handleDelete(row)">删除</NButton>
        </NSpace>
      </template>
    </Grid>

    <Modal>
      <div style="display: flex; flex-direction: column; gap: 16px; padding: 8px 0">
        <div>
          <label style="display: block; margin-bottom: 4px">昵称</label>
          <NInput v-model:value="editForm.nickname" placeholder="昵称" />
        </div>
        <div>
          <label style="display: block; margin-bottom: 4px">邮箱</label>
          <NInput v-model:value="editForm.email" placeholder="邮箱" />
        </div>
        <div>
          <label style="display: block; margin-bottom: 4px">角色</label>
          <NSelect v-model:value="editForm.role_id" :options="roleOptions" placeholder="选择角色" clearable />
        </div>
      </div>
    </Modal>
  </Page>
</template>
