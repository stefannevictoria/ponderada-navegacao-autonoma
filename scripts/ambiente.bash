# Carregue com: source scripts/ambiente.bash
_PONDERADA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$_PONDERADA_ROOT/.venv/bin/activate"
_PONDERADA_SITE="$("$_PONDERADA_ROOT/.venv/bin/python" -c 'import sysconfig; print(sysconfig.get_path("purelib"))')"
export PYTHONPATH="$_PONDERADA_SITE${PYTHONPATH:+:$PYTHONPATH}"
if [ -f "$_PONDERADA_ROOT/simulador/install/setup.bash" ]; then
    source "$_PONDERADA_ROOT/simulador/install/setup.bash"
fi
unset _PONDERADA_ROOT _PONDERADA_SITE
