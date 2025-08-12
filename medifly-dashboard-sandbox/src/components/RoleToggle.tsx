import { RoleKey } from '../data/types';
import { useNavigate, useSearchParams } from 'react-router-dom';

const roles: RoleKey[] = ['affiliate','provider','individual'];

export default function RoleToggle() {
  const nav = useNavigate();
  const [sp] = useSearchParams();
  const role = (sp.get('role') as RoleKey) || 'provider';

  function setRole(r: RoleKey){ 
    const qp = new URLSearchParams(sp);
    qp.set('role', r);
    nav({ search: qp.toString() }, { replace: true });
  }

  return (
    <div className="inline-flex rounded-md border overflow-hidden role-toggle" role="tablist" data-test="role-toggle">
      {roles.map(r=>(
        <button key={r} role="tab"
          onClick={()=>setRole(r)}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            r===role
              ? 'bg-blue-600 text-white' 
              : 'bg-white hover:bg-gray-50 text-gray-700'
          }`}>
          {r[0].toUpperCase()+r.slice(1)}
        </button>
      ))}
    </div>
  );
}