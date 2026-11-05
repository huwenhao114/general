// 仓库元数据
const REPO_META = {
  'Smart-Visitor-Flow-and-Service-Scheduling-System-for-Qinglu-Scenic-Area': {
    desc: '景区客流与服务调度', lang: 'HTML', langColor: '#e34c26', updated: '2026-11-05'
  },
  'Smart-Hotel-Room-Status-Check-in-Collaboration-System': {
    desc: 'FDE-面向酒店行业的数智化转型解决方案', lang: 'HTML', langColor: '#e34c26', updated: '2026-10-29'
  },
  'license-certification-quiz': {
    desc: '许可核验的测试', lang: 'HTML', langColor: '#e34c26', updated: '2026-10-29'
  },
  '-ai-': {
    desc: '"校园学习助手"智能体源代码及其演示html格式幻灯片', lang: 'JavaScript', langColor: '#f1e05a', updated: '2026-10-25'
  },
  'exam-review-plan': {
    desc: '考试倒计时复习计划', lang: 'TypeScript', langColor: '#3178c6', updated: '2026-10-14'
  },
  'openclaw1': {
    desc: 'openclaw代码', lang: 'Python', langColor: '#3572A5', updated: '2026-10-13'
  },
  'openclaw': {
    desc: 'openclaw原理代码', lang: '', langColor: '#ccc', updated: '2026-10-13'
  },
  'process2-': {
    desc: 'process2（项目二）', lang: '', langColor: '#ccc', updated: '2026-10-09'
  },
  '-': {
    desc: '项目三 学生上课签到软件', lang: 'TypeScript', langColor: '#3178c6', updated: '2026-10-08'
  }
};

const LANG_COLORS = {
  'HTML': '#e34c26', 'CSS': '#563d7c', 'JavaScript': '#f1e05a',
  'TypeScript': '#3178c6', 'Python': '#3572A5', 'Java': '#b07219',
  'C': '#555555', 'C++': '#f34b7d', 'Vue': '#41b883', 'Markdown': '#083fa1'
};

// 路由
function navigate(hash) {
  location.hash = hash;
}

window.addEventListener('hashchange', render);
window.addEventListener('load', render);

function render() {
  const hash = location.hash.slice(1);
  const content = document.getElementById('content');
  const breadcrumb = document.getElementById('breadcrumb');

  if (!hash) {
    // 仓库列表
    breadcrumb.innerHTML = '<span>Repositories</span>';
    renderRepoList();
  } else if (hash.startsWith('repo/')) {
    const parts = hash.slice(5).split('?file=');
    const repo = decodeURIComponent(parts[0]);
    const filePath = parts[1] ? decodeURIComponent(parts[1]) : null;
    if (filePath) {
      breadcrumb.innerHTML = `<a href="#" onclick="navigate('');return false;">Repositories</a> / <a href="#repo/${encodeURIComponent(repo)}" onclick="return false;">${repo}</a> / ${filePath}`;
      renderFile(repo, filePath);
    } else {
      breadcrumb.innerHTML = `<a href="#" onclick="navigate('');return false;">Repositories</a> / ${repo}`;
      renderRepo(repo);
    }
  } else {
    renderRepoList();
  }
}

// 仓库列表
function renderRepoList() {
  const content = document.getElementById('content');
  const repos = Object.keys(REPO_META).sort((a, b) =>
    new Date(REPO_META[b].updated) - new Date(REPO_META[a].updated)
  );

  let html = '<div class="repo-list">';
  for (const repo of repos) {
    const meta = REPO_META[repo];
    const files = (window.REPO_INDEX && window.REPO_INDEX[repo]) || [];
    const fileCount = files.length;
    html += `
      <div class="repo-item">
        <div>
          <div class="repo-name" onclick="navigate('repo/${encodeURIComponent(repo)}')">${repo}</div>
          <div class="repo-desc">${meta.desc || 'No description'}</div>
          <div class="repo-meta">
            ${meta.lang ? `<span><span class="lang-dot" style="background:${meta.langColor}"></span>${meta.lang}</span>` : ''}
            <span>📁 ${fileCount} 文件</span>
            <span>🕐 ${meta.updated}</span>
          </div>
        </div>
        <div class="repo-stats">
          <span>📄 ${fileCount}</span>
        </div>
      </div>`;
  }
  html += '</div>';
  content.innerHTML = html;
}

// 仓库详情（文件树）
function renderRepo(repo) {
  const content = document.getElementById('content');
  const files = (window.REPO_INDEX && window.REPO_INDEX[repo]) || [];
  const meta = REPO_META[repo] || {};

  if (files.length === 0) {
    content.innerHTML = `<div class="file-browser"><div class="file-header"><strong>${repo}</strong></div><div class="error" style="padding:24px;">此仓库为空</div></div>`;
    return;
  }

  // 构建目录树
  const tree = buildTree(files);

  let html = `
    <div style="margin-bottom:16px;">
      <h2 style="font-size:20px;">${repo}</h2>
      <p style="color:#8b949e;margin-top:4px;">${meta.desc || ''}</p>
    </div>
    <div class="file-browser">
      <div class="file-header"><strong>📁 Files</strong><span>${files.length} files</span></div>
      <ul class="file-list">
        ${renderTreeNode(tree, repo, '')}
      </ul>
    </div>`;

  // 查找 README
  const readme = files.find(f => /^readme(\.md)?$/i.test(f.path.split('/').pop()));
  if (readme) {
    html += `<div class="readme"><div class="code-header"><strong>📖 README</strong></div><div class="readme-body" id="readme-content"><div class="loading">加载中...</div></div></div>`;
    loadReadme(repo, readme.path);
  }

  content.innerHTML = html;
}

function buildTree(files) {
  const tree = {};
  for (const f of files) {
    const parts = f.path.split('/');
    let node = tree;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i === parts.length - 1) {
        node[part] = { __file: true, path: f.path, size: f.size };
      } else {
        if (!node[part]) node[part] = {};
        node = node[part];
      }
    }
  }
  return tree;
}

function renderTreeNode(node, repo, prefix) {
  let html = '';
  const entries = Object.entries(node).sort((a, b) => {
    const aDir = !a[1].__file, bDir = !b[1].__file;
    if (aDir !== bDir) return bDir ? 1 : -1;
    return a[0].localeCompare(b[0]);
  });
  for (const [name, val] of entries) {
    if (val.__file) {
      const icon = getFileIcon(name);
      html += `<li onclick="navigate('repo/${encodeURIComponent(repo)}?file=${encodeURIComponent(val.path)}')">
        <span class="file-icon">${icon}</span>
        <span class="file-name">${prefix}${name}</span>
        <span class="file-size">${formatSize(val.size)}</span>
      </li>`;
    } else {
      html += `<li class="dir" onclick="event.stopPropagation();toggleDir(this)">
        <span class="file-icon">📁</span>
        <span class="file-name">${prefix}${name}/</span>
      </li>`;
    }
  }
  return html;
}

function toggleDir(li) {
  // 简单展开/折叠目录（预留）
  li.style.opacity = li.style.opacity === '0.5' ? '1' : '0.5';
}

function getFileIcon(name) {
  const ext = name.split('.').pop().toLowerCase();
  const icons = {
    'js': '📜', 'ts': '📜', 'html': '🌐', 'css': '🎨', 'json': '⚙️',
    'md': '📖', 'py': '🐍', 'java': '☕', 'c': 'C', 'cpp': 'C++',
    'vue': '💚', 'png': '🖼️', 'jpg': '🖼️', 'gif': '🖼️', 'svg': '🖼️',
    'zip': '📦', 'pdf': '📕', 'txt': '📄'
  };
  return icons[ext] || '📄';
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}

// 文件查看
function renderFile(repo, filePath) {
  const content = document.getElementById('content');
  const fileName = filePath.split('/').pop();
  const ext = fileName.split('.').pop().toLowerCase();
  const textExts = ['js', 'ts', 'html', 'css', 'json', 'md', 'py', 'java', 'c', 'cpp', 'h', 'vue', 'txt', 'xml', 'yml', 'yaml', 'sh', 'bat', 'sql', 'gitignore'];

  if (textExts.includes(ext) || !ext) {
    content.innerHTML = `
      <div class="file-browser">
        <div class="file-header"><strong>📄 ${filePath}</strong><span>${formatSize(getFileSize(repo, filePath))}</span></div>
      </div>
      <div class="code-view">
        <div class="code-header"><span>${fileName}</span><span class="back-btn" onclick="navigate('repo/${encodeURIComponent(repo)}')">← 返回</span></div>
        <pre><code id="file-code"><div class="loading">加载中...</div></code></pre>
      </div>`;
    loadFile(repo, filePath);
  } else {
    content.innerHTML = `
      <div class="file-browser">
        <div class="file-header"><strong>🖼️ ${filePath}</strong><span class="back-btn" onclick="navigate('repo/${encodeURIComponent(repo)}')">← 返回</span></div>
      </div>
      <div style="text-align:center;padding:24px;">
        <img src="repos/${encodeURIComponent(repo)}/${filePath}" style="max-width:100%;border-radius:6px;" onerror="this.parentElement.innerHTML='<div class=\\'error\\'>无法预览此文件</div>'">
      </div>`;
  }
}

function getFileSize(repo, filePath) {
  const files = window.REPO_INDEX[repo] || [];
  const f = files.find(x => x.path === filePath);
  return f ? f.size : 0;
}

async function loadFile(repo, filePath) {
  try {
    const res = await fetch(`repos/${encodeURIComponent(repo)}/${filePath}`);
    const text = await res.text();
    const code = document.getElementById('file-code');
    const lines = text.split('\n');
    code.innerHTML = lines.map((line, i) =>
      `<span class="line-numbers">${i + 1}</span>${escapeHtml(line)}\n`
    ).join('');
  } catch (e) {
    document.getElementById('file-code').innerHTML = '<div class="error">加载失败: ' + e.message + '</div>';
  }
}

async function loadReadme(repo, filePath) {
  try {
    const res = await fetch(`repos/${encodeURIComponent(repo)}/${filePath}`);
    const text = await res.text();
    const el = document.getElementById('readme-content');
    el.innerHTML = renderMarkdown(text);
  } catch (e) {
    document.getElementById('readme-content').innerHTML = '<div class="error">README 加载失败</div>';
  }
}

// 简易 Markdown 渲染
function renderMarkdown(text) {
  let html = escapeHtml(text);
  html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
  html = html.replace(/^- (.*$)/gm, '<li>$1</li>');
  html = html.replace(/(\n<li>.*<\/li>\n?)+/g, m => '<ul>' + m + '</ul>');
  html = html.replace(/\n/g, '<br>');
  return html;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
