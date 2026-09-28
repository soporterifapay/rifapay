import React from 'react'
import { renderToString } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'
import { ToastHost } from './src/components/ui.jsx'
import App from './src/App.jsx'
import Home from './src/pages/Home.jsx'
import RaffleDetail from './src/pages/RaffleDetail.jsx'
import Checkout from './src/pages/Checkout.jsx'
import Login from './src/pages/Login.jsx'
import Dashboard from './src/pages/Dashboard.jsx'
import Admin from './src/pages/Admin.jsx'

const wrap = (el, route = '/') => renderToString(
  React.createElement(ToastHost, null,
    React.createElement(MemoryRouter, { initialEntries: [route] }, el)))

const cases = [
  ['App', React.createElement(App)],
  ['Home', React.createElement(Home)],
  ['RaffleDetail', React.createElement(RaffleDetail), '/rifa/abc'],
  ['Checkout', React.createElement(Checkout), '/orden/abc'],
  ['Login', React.createElement(Login)],
  ['Dashboard', React.createElement(Dashboard)],
  ['Admin', React.createElement(Admin)],
]
let fail = 0
for (const [name, el, route] of cases) {
  try {
    wrap(el, route)
    console.log('OK  ', name)
  } catch (e) {
    fail++
    console.log('FAIL', name, '-', e.message.split('\n')[0])
  }
}
if (fail) process.exit(1)
console.log('SMOKE OK')
