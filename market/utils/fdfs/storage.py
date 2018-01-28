from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client
import os

class FDFSStorage(Storage):
    """FDFS文件系统存储类"""
    def __init__(self, client_conf=None, nginx_url=None):
        """初始化"""
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if nginx_url is None:
            nginx_url = settings.FDFS_NGINX_URL
        self.nginx_url = nginx_url

    # 重写save方法
    def _save(self,name, content):
        # name 上传文件的名称
        # 读取内容
        content = content.read()
        #创建实例对象 client
        # return dict
        # {
        #     'Group name': group_name,
        #     'Remote file_id': remote_file_id,
        #     'Status': 'Upload successed.',
        #     'Local file name': local_file_name,
        #     'Uploaded size': upload_size,
        #     'Storage IP': storage_ip
        # } if success else None
        client = Fdfs_client(os.path.join(settings.BASE_DIR, 'utils/fdfs/client.conf'))
        # 上传内容
        response = client.upload_by_buffer(content)
        # 返回响应值
        if response is None or response.get('Status') != 'Upload successed.':
            print(response)
            print(response.get('Status'))
            # 上传失败，跑出异常
            raise Exception('上传文件到FDFS系统失败')
        file_id = response.get('Remote file_id')
        return file_id

    def exists(self, name):
        return False

    def url(self, name):
        return self.nginx_url + name
