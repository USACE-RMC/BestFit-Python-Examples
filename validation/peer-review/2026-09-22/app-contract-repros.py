"""Read-only review probes: no model runs, repository writes, or estimation."""
from pathlib import Path
import argparse
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bestfit-source', type=Path, required=True)
ROOT = parser.parse_args().bestfit_source.resolve()
sys.path.insert(0, str(ROOT / 'skills/bestfit-frequency'))
from bestfit_plots.adapters.api_response_models import response_plots
from bestfit_plots.spec import validate_spec

dates = ['2000-01-01T00:00:00', '2000-01-02T00:00:00', '2000-01-03T00:00:00']
snapshot = dict(state='succeeded', analysisId='review-probe', lastRunUtc='2026-09-22T12:00:00Z',
    kind='timeSeries', resultDates=dates,
    series=[dict(name='observed', points=[dict(date=d, value=v) for d,v in zip(dates,[10.,11.,'NaN'])])],
    residualPlot=dict(residuals=[-1.,1.], dates=dates[:2],
        histogram=[dict(lowerBound=-2., upperBound=2., frequency=2.)],
        qq=[dict(x=-1.,y=-1.),dict(x=1.,y=1.)]),
    results=dict(trainingTimeSteps=2, curve=dict(modeCurve=[10.,11.,12.], meanCurve=[10.,11.,12.],
        ciLower=[9.,10.,11.],ciUpper=[11.,12.,13.],credibleIntervalWidth=.9)))
plots = response_plots(snapshot)
try:
    validate_spec(plots['series'])
except ValueError as exc:
    print('NaN wire-value rejection:', str(exc))
snapshot['series'][0]['points'][2]['value'] = None
validate_spec(response_plots(snapshot)['series'])
print('Equivalent null gap: accepted')

from pythonnet import load
binpath = ROOT / 'src/RMC.BestFit.Api/bin/Release/net10.0'
load('coreclr', runtime_config=str(binpath / 'RMC.BestFit.Api.runtimeconfig.json'))
import clr
clr.AddReference(str(binpath / 'RMC.BestFit.Api.dll'))
from RMC.BestFit.Api.DTOs import PlotSourceResponse
from RMC.BestFit.Api.Mcp import McpJson
response = PlotSourceResponse()
response.Success = False
response.ErrorMessage = 'No completed run'
print('Failure Results ValueKind:', response.Results.ValueKind)
try:
    print(McpJson.Serialize[PlotSourceResponse](response))
except Exception as exc:
    print('Failure serialization:', type(exc).__name__, str(exc))
