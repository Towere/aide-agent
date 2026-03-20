<template>
  <el-container class="app-container">
    <el-header>
      <h1>📄 代码转论文智能体</h1>
    </el-header>
    <el-main>
      <Home />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import Home from './views/Home.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.app-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.app-container .el-header {
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 40px;
}

.app-container .el-header h1 {
  font-size: 24px;
}

.app-container .el-main {
  max-width: 1000px;
  margin: 40px auto;
}
</style>
