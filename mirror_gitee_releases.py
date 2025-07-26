### 3. 源代码同步（返回是否有文件更新）
def sync_source_code(tag_name, target_release, synced_data):
    if not target_release:
        print(f"错误：target_release 为 None，无法同步源代码 {tag_name}")
        return False
    
    print(f"\n===== 同步源代码: {tag_name} =====")
    # 使用 Gitee API 提供的源代码下载链接格式
    source_files = {
        f"SourceCode_{tag_name}.zip": 
            f"https://gitee.com/api/v5/repos/{SOURCE_OWNER}/{SOURCE_REPO_NAME}/archive/{tag_name}.zip",
        f"SourceCode_{tag_name}.tar.gz": 
            f"https://gitee.com/api/v5/repos/{SOURCE_OWNER}/{SOURCE_REPO_NAME}/archive/{tag_name}.tar.gz"
    }
    
    # 如果提供了 token，添加到 URL 参数中
    if SOURCE_GITEE_TOKEN:
        for filename in source_files:
            source_files[filename] += f"?access_token={SOURCE_GITEE_TOKEN}"
    
    existing_assets = {a.name: a for a in target_release.get_assets()}
    synced_data['source_codes'].setdefault(tag_name, {})
    has_changes = False  # 标记是否有文件更新
    
    for filename, url in source_files.items():
        if filename in existing_assets:
            print(f"目标仓库已存在 {filename}，跳过")
            if filename not in synced_data['source_codes'][tag_name]:
                synced_data['source_codes'][tag_name][filename] = {
                    'exists': True,
                    'synced_at': str(datetime.datetime.now())
                }
                save_synced_data(synced_data)
            continue
        
        # 目标不存在，需要同步（属于更新）
        print(f"目标仓库缺失 {filename}，开始同步")
        temp_path = f"temp_{filename}"
        try:
            # 使用新的下载函数，支持带 token 的 URL
            download_file_with_token(url, temp_path)
            uploaded_asset = retry_upload(
                target_release, temp_path, filename, "application/zip"
            )
            
            if uploaded_asset:
                synced_data['source_codes'][tag_name][filename] = {
                    'exists': True,
                    'synced_at': str(datetime.datetime.now())
                }
                save_synced_data(synced_data)
                print(f"同步成功 {filename}")
                has_changes = True  # 标记有更新
            else:
                print(f"同步 {filename} 失败")
        except Exception as e:
            print(f"处理 {filename} 失败: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    print(f"===== 源代码同步完成: {tag_name} =====")
    return has_changes  # 返回是否有更新


### 5. 辅助函数与主函数
def download_file_with_token(url, save_path):
    """专门用于下载源代码文件的函数，支持带 token 的 URL"""
    if os.path.exists(save_path):
        print(f"文件已存在: {save_path}，跳过下载")
        return save_path
    
    try:
        print(f"开始下载: {url}")
        resp = requests.get(url, stream=True, timeout=600)
        resp.raise_for_status()
        
        with open(save_path, 'wb') as f:
            total_size = int(resp.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 8192
            
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if downloaded % (10 * 1024 * 1024) < chunk_size and total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"下载进度: {downloaded//(1024*1024):d}MB / {total_size//(1024*1024):d}MB ({percent:.1f}%)")
        
        print(f"下载成功: {save_path}（{os.path.getsize(save_path)} 字节）")
        return save_path
    except Exception as e:
        print(f"下载失败: {str(e)}")
        if os.path.exists(save_path):
            os.remove(save_path)
        raise
