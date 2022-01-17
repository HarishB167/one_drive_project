import base64
import requests
from pprint import pprint
from pathlib import Path

class OneDrive_Browser:

  def __init__(self, shared_link, verbose=False):
    self.verbose = verbose
    self.shared_link = shared_link
    self.check_if_folder(self.shared_link)
    self.download_folder = "Downloads"
    self.sub_folder_dir = self.download_folder + "/sub_folder_files"
    self.all_subdir_files_in_one_dir = True

  def vprint(self, text):
    if self.verbose: print(text)

  # Ref : https://towardsdatascience.com/how-to-get-onedrive-direct-download-link-ecb52a62fee4
  # Ref : https://stackoverflow.com/questions/36015295/downloading-a-publicly-shared-file-from-onedrive
  # Ref : https://docs.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_list_children?view=odsp-graph-online
  def create_onedrive_pathdetails_link(self, onedrive_link):
    data_bytes64 = base64.b64encode(bytes(onedrive_link, 'utf-8'))
    data_bytes64_String = data_bytes64.decode('utf-8').replace('/','_').replace('+','-').rstrip("=")
    resultUrl = f"https://api.onedrive.com/v1.0/shares/u!{data_bytes64_String}/root"
    return resultUrl

  def check_if_folder(self, shared_link):
    link = self.create_onedrive_pathdetails_link(shared_link)
    print(link)
    r = requests.get(link)
    if r.status_code == 200:
      self.vprint("check_if_folder 1 : Status code 200")
    else:
      self.vprint(f"Error occured in check_if_folder 1 : {r.status_code}")
      self.vprint(str(r.content))
    json_output = r.json()
    # print(json_output.keys())
    if 'folder' in json_output.keys():
      child_count = json_output['folder']['childCount']
      name = json_output['name']
      size = json_output['size']
      self.vprint(f'Path type is folder, childcount : {child_count}, name : {name}, size : {size}')
      return True
    elif 'file' in json_output.keys():
      filename = json_output['name']
      size = json_output['size']
      self.vprint(f"Path type is file, name : {filename}, size : {size}")
      return False
    return False

  def get_file_details(self, json_val):
    path_type = "file" if "file" in json_val.keys() else "folder"
    name = json_val['name']
    size = json_val['size']
    link = json_val['webUrl']
    return [path_type, name, size, link]
    

  def get_childs(self, shared_link):
    link = self.create_onedrive_pathdetails_link(shared_link)
    link += "/children"
    print(link)
    r = requests.get(link)
    if r.status_code == 200:
      self.vprint("get_childs 1 : Status code 200")
    else:
      self.vprint(f"Error occured in get_childs 1 : {r.status_code}")
      self.vprint(str(r.content))
    json_output = r.json()
    # print(json_output)
    childs_details_raw = json_output['value']
    childs_details = []
    for row in childs_details_raw:
      result = self.get_file_details(row)
      if result[0] == "folder":
        sub_childs = self.get_childs(result[3])
        result.append(sub_childs)
      childs_details.append(result)
    # pprint(childs_details)

    return childs_details

  def ensure_folder_exists(self, dir):
    Path(dir).mkdir(parents=True, exist_ok=True)

  def ensure_download_folder_exists(self):
    Path(self.download_folder).mkdir(parents=True, exist_ok=True)
    if self.all_subdir_files_in_one_dir:
      Path(self.sub_folder_dir).mkdir(parents=True, exist_ok=True)

  def _download_files(self, file_tree, current_dir):
    if current_dir == self.download_folder:
      dir = self.download_folder
    else:
      if self.all_subdir_files_in_one_dir:
        dir = self.sub_folder_dir
      else:
        dir = current_dir
    for row in file_tree:
      if row[0] == "file":
        url = self.create_onedrive_pathdetails_link(row[3]) + "/content"
        r = requests.get(url)
        path = dir + "/" + row[1]
        self.ensure_folder_exists(dir)
        with open(path, 'wb') as f:
          f.write(r.content)
          print(f"Saved as {path}")
      elif row[0] == "folder":
        sub_file_tree = row[4]
        sub_dir = self.sub_folder_dir if self.all_subdir_files_in_one_dir else\
                  f"{dir}/{row[1]}"
        self._download_files(sub_file_tree, sub_dir)
      print(row)

  def scan_folder(self):
    if not self.check_if_folder(self.shared_link):
      print(f"Not a folder : {self.shared_link}")
      return
    
    self.file_tree = self.get_childs(self.shared_link)
    pprint(self.file_tree)

  def download_all_files(self):
    self.ensure_download_folder_exists()
    self._download_files(self.file_tree, self.download_folder)

if __name__ == "__main__":
  shared_link = "https://1drv.ms/p/s!BOkKr2xV9XySdkj8ToXsbXlRfKY"
  folder = "https://1drv.ms/a/s!BOkKr2xV9XySdWsQBEHbiLJf3Xc"
  folder2 = "https://1drv.ms/f/s!BOkKr2xV9XySgQRrEARB24iyX913"
  worker = OneDrive_Browser(folder, verbose=True)
  worker.scan_folder()
  worker.download_all_files()
