.pragma library

// Plugin-owned service handoff to this plugin's visual components. A custom
// bar receives no generic host service lookup; the plugin opts into sharing
// only its own service here. Never store the host shell or an auth service.
var current = null
var subscribers = []

function subscribe(widget) {
  if (subscribers.indexOf(widget) === -1) subscribers.push(widget)
  widget.sharedService = current
}
function unsubscribe(widget) {
  subscribers = subscribers.filter(function(candidate) { return candidate && candidate !== widget })
}
function publish(service) {
  current = service
  subscribers = subscribers.filter(function(widget) { return !!widget })
  for (var i = 0; i < subscribers.length; i++) subscribers[i].sharedService = service
}
function release(service) {
  // A retired hot-reload instance must not clear its replacement.
  if (current === service) publish(null)
}
