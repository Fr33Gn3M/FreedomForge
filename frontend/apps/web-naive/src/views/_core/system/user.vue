<script lang="ts" setup>
import type { VxeGridProps } from '#/adapter/vxe-table';

import { ref } from 'vue';

import { Page } from '@vben/common-ui';
import { useVbenModal } from '@vben-core/popup-ui';

import { NButton, NSpace, NTag } from 'naive-ui';

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
    toolbarConfig: {
      buttons: [],
    },
    proxyConfig: {
      ajax: {
        query: async ({ page }) => {
          const res = await getUserListApi({
            page: page.currentPage,
            page_size: page.pageSize,
          });
          return { items: res.list, total: res.total };
        },
      },
    },
  },
});

// ====== Edit modal ======
const editForm = ref({ id: 0, nickname: '', email: '', role_id: null as number | null });
const roleOptions = ref<{ label: string; value: number }[]>([]);

const [Modal, modalApi] = useVbenModal({
  title: '编辑用户',
  onOpenChange: async (isOpen) => {
    if (isOpen) {
      const row = modalApi.getData<Record<string, any>>();
      editForm.value = {
        id: row.id,
        nickname: row.nickname || '',
        email: row.email || '',
        role_id: row.role_id || null,
      };
      const roles = await getAllRolesApi();
      roleOptions.value = roles.map((r: any) => ({ label: r.name, value: r.id }));
    }
  },
  onConfirm: async () => {
    await updateUserApi(editForm.value.id, {
      nickname: editForm.value.nickname,
      email: editForm.value.email,
      role_id: editForm.value.role_id,
    });
    gridApi?.reload();
    modalApi.close();
  },
});

function openEdit(row: Record<string, any>) {
  modalApi.setData(row).open();
}

// ====== Delete ======
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
          <NButton type="primary" size="small" @click="gridApi?.reload()">
            刷新
          </NButton>
        </NSpace>
      </template>

      <template #role_name="{ row }">
        <NTag :type="row.role_code === 'super' ? 'error' : row.role_code === 'admin' ? 'warning' : 'info'" size="small">
          {{ row.role_name }}
        </NTag>
      </template>

      <template #action="{ row }">
        <NSpace>
          <NButton size="tiny" type="primary" quaternary @click="openEdit(row)">
            编辑
          </NButton>
          <NButton size="tiny" type="error" quaternary
            :disabled="row.role_code === 'super'"
            @click="handleDelete(row)">
            删除
          </NButton>
        </NSpace>
      </template>
    </Grid>

    <Modal>
      <div style="display:flex;flex-direction:column;gap:16px;padding:8px 0">
        <div>
          <label>昵称</label>
          <input v-model="editForm.nickname" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px" />
        </div>
        <div>
          <label>邮箱</label>
          <input v-model="editForm.email" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px" />
        </div>
        <div>
          <label>角色</label>
          <select v-model="editForm.role_id" style="width:100%;padding:8px;border:1px solid #d9d9d9;border-radius:4px">
            <option :value="null">-- 无角色 --</option>
            <option v-for="r in roleOptions" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
        </div>
      </div>
    </Modal>
  </Page>
</template>
