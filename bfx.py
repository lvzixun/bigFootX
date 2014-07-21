import urllib
import zipfile
import sys
import io
import os
import json
import xml.etree.ElementTree as ET


class bigFootX(object):
  # the addons update files xml url
  filelist_url = "http://bfupdatedx.178.com/BigFoot/Interface/3.1/filelist.xml"

  # the all addons files prefix url
  addons_prefix_url = "http://bfupdatedx.178.com/BigFoot/Interface/3.1/Interface/AddOns/"

  up_filelist_dict = False

  def __init__(self, wow_dir):
    self.wow_dir = os.path.expanduser(wow_dir)


    local_filelist_path = os.path.join(self.wow_dir, "Interface", "filelist.json")
    self.local_filst_data = {}
    if os.path.exists(local_filelist_path):
      self.local_filst_data = json.loads(open(local_filelist_path).read())


  # get the new file list from web
  def _get_up_filelist(self):
    if not self.up_filelist_dict:
      filelist_data = self._open_zurl(self.filelist_url)
      self.up_filelist_dict = self._xml2dict(filelist_data)
    return self.up_filelist_dict


  def _xml2dict(self, xml_data):
    ret = {}
    root = ET.fromstring(xml_data)
    for addon in root:
      item = {
        'name': addon.attrib['name'],
        'title': addon.attrib['Title-zhCN'],
        'files':{}
      }

      files = item['files']
      for f in addon:
        files[f.attrib['path']] = f.attrib['checksum']

      ret[item['name']] = item

    return ret


  def _diff_filelist(self, up_dict):
    ret = []
    for k, v in up_dict.iteritems():
      has_key = self.local_filst_data.has_key(k)
      local_files = False
      if has_key:
        local_files = self.local_filst_data[k]['files']
      for fk, fv in v['files'].iteritems():
        if not local_files or  not local_files.has_key(fk) or local_files[fk] != fv:
          ret.append(os.path.join(k, fk.replace("\\", "/")))

    return ret

  def diff(self):
    up_dict = self._get_up_filelist()
    return self._diff_filelist(up_dict)
  

  def _write_file(self, path, data):
    dirs = path.split('/')
    dp = self.wow_dir
    for x in xrange(len(dirs)-1):
      dp = os.path.join(dp, dirs[x])
      if not os.path.exists(dp):
        os.mkdir(dp)

    handle = open(os.path.join(self.wow_dir, path), "w")
    handle.write(data)
    handle.close()


  def decompress(self, file_name):
    data = self._open_zurl(
      os.path.join(self.addons_prefix_url, file_name))

    target = os.path.join('Interface', 'AddOns', file_name)
    self._write_file(target, data)


  def _open_zurl(self, url):
    handle = urllib.urlopen(url+".z")
    z_data = handle.read()
    z_obj = io.BytesIO(z_data)
    z_handle = zipfile.ZipFile(z_obj)

    return z_handle.read(os.path.basename(url))

  def update(self):
    print("get filelist...")
    diff = self.diff()

    max = len(diff)
    cur = 1
    for f in diff:
      print("update: "+ f + ("    [%d/%d]" % (cur, max)))
      self.decompress(f)
      cur += 1

    print("write filelist...")
    filelist_path = os.path.join("Interface", "filelist.json")
    json_str = json.dumps(self.up_filelist_dict)
    self._write_file(filelist_path, json_str)


argv = sys.argv

if len(argv) <2:
  print "python bfx.py <wow dir>"
  exit(0)


bf = bigFootX(argv[1])
bf.update()



