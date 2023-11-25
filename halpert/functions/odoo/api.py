import xmlrpc.client
from dataclasses import dataclass
from typing import List, Dict, Any, TypeVar, Type, cast


class OdooAPI:
  url = 'http://localhost:8069'
  username = 'admin'
  password = 'admin'
  db = 'odoo'
  user_id: int


  def __init__(self):
    self.user_id = self._get_user_id()


  def _get_user_id(self) -> int:
    common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
    user_id = common.authenticate(self.db, self.username, self.password, {})
    return user_id


  def _request(self, model: str, op: str, args: List, options: Dict = {}):
    models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
    return models.execute_kw(self.db, self.user_id, self.password, model, op, args, options)


  @dataclass
  class SearchFilter:
    field: str
    operator: str
    value: Any

    def to_odoo(self) -> List[Any]:
      return [self.field, self.operator, self.value]


  def search_read(
    self,
    model: str,
    fields: List[str],
    filters: List[SearchFilter] = [],
  ) -> List[Dict]:
    return self._request(
      model, 'search_read',
      [[f.to_odoo() for f in filters]],
      { 'fields': fields },
    )


  @dataclass
  class AttendeeDetail:
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
