import { useState, useEffect } from 'react'

function App() {
  const [tenants, setTenants] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [errorDetalle, setErrorDetalle] = useState(null);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/v1/tenants/')
      .then(async (res) => {
        if (!res.ok) {
          const dataError = await res.json().catch(() => ({}));
          throw new Error(`HTTP ${res.status}: ${dataError.detail || res.statusText || 'Acceso restringido o error en la petición'}`);
        }
        return res.json();
      })
      .then((data) => {
        const lista = Array.isArray(data) ? data : (data.results || []);
        setTenants(lista);
        setCargando(false);
      })
      .catch((err) => {
        console.error('Detalle del error:', err);
        setErrorDetalle(err.message);
        setCargando(false);
      });
  }, []);

  return (
    <div style={{ padding: '30px', fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <h1>SaaS Escolar B2B - Control Panel</h1>
      
      <div style={{ marginTop: '20px', padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
        <h2>Instituciones / Tenants Registrados</h2>

        {cargando && <p>Cargando información desde Django...</p>}
        
        {errorDetalle && (
          <div style={{ padding: '12px', backgroundColor: '#fee2e2', border: '1px solid #fca5a5', borderRadius: '6px', color: '#991b1b' }}>
            <p style={{ margin: 0 }}><strong>Respuesta de Django:</strong> {errorDetalle}</p>
          </div>
        )}

        {!cargando && !errorDetalle && tenants.length === 0 && (
          <p>La conexión funciona correctamente, pero la tabla está vacía.</p>
        )}

        {!cargando && !errorDetalle && tenants.length > 0 && (
          <ul>
            {tenants.map((item, index) => (
              <li key={item.id || index}>
                <strong>{item.nombre || item.name || item.domain || JSON.stringify(item)}</strong>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default App