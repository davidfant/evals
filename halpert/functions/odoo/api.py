import xmlrpc.client
from pydantic import BaseModel
from typing import List, Dict, Any
from enum import Enum


class OdooAPI:
  url = 'http://localhost:8069'
  username = 'admin'
  password = 'admin'
  db = 'odoo'
  user_id: int


  class Command(Enum):
    CREATE = 0
    UPDATE = 1
    DELETE = 2
    UNLINK = 3
    LINK = 4
    CLEAR = 5
    SET = 6


  def __init__(self):
    self.user_id = self._get_user_id()


  def _get_user_id(self) -> int:
    common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
    user_id = common.authenticate(self.db, self.username, self.password, {})
    return user_id
  

  def _fields_to_specification(self, fields: List[str]) -> Dict[str, Dict]:
    specification: Dict[str, Dict] = {}
    for field in fields:
      field_spec = specification
      parts = field.split('.')
      for part_idx, part in enumerate(parts):
        if part not in field_spec:
          field_spec[part] = {}

        is_last = part_idx == len(parts) - 1
        if not is_last:
          field_spec[part]['fields'] = {}
          field_spec = field_spec[part]['fields']
    return specification


  def _request(self, model: str, op: str, args: List, options: Dict = {}):
    models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
    return models.execute_kw(self.db, self.user_id, self.password, model, op, args, options)


  class SearchFilter(BaseModel):
    field: str
    op: str
    value: Any

    def to_odoo(self) -> List[Any]:
      return [self.field, self.op, self.value]

  def search_read(
    self,
    model: str,
    fields: List[str],
    filters: List[SearchFilter] = [],
  ) -> List[Dict]:
    response = self._request(
      model, 'web_search_read',
      [[f.to_odoo() for f in filters]],
      { 'specification': self._fields_to_specification(fields) },
    )
    return response['records']
  

  def create(
    self,
    model: str,
    data: Dict[str, Any],
    fields: List[str],
  ) -> Dict:
    response = self._request(
      model, 'web_save',
      [[], data],
      { 'specification': self._fields_to_specification(fields) },
    )
    return response[0]


  class AttendeeDetail(BaseModel):
    id: int
    name: str
    status: str
    is_organizer: bool

  def get_attendee_detail(self, partner_ids: List[int], model_id: int) -> List[AttendeeDetail]:
    if not partner_ids:
      return []
    details = self._request(
      'res.partner', 'get_attendee_detail',
      [partner_ids, [model_id]],
    )
    return [
      self.AttendeeDetail(
        id=detail['id'],
        name=detail['name'],
        status=detail['status'],
        is_organizer=bool(detail['is_organizer']),
      )
      for detail in details
    ]
