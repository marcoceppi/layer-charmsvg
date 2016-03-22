# Overview

This deploys the Juju SVG web service. This service, when deployed, will
generage SVGs once fed a valid bundle.

# Usage

This charm is mostly standalone and self contained.

    juju deploy charm-svg
    juju expose charm-svg

Once deployed and exposed, any web requests can be made against the
[HTTP endpoint](http://svg.juju.solutions) to generate an SVG.

## Resources and Upgrading

This charm makes use of resources, a feature only available in Juju 2.0. During
deploy or at upgrade time you can replace the following resources for newer
ones:

### python-jujusvg

This is the binary used to generate the SVGs given a bundle. The python-jujusvg
builds upon the [jujusvg](https://github.com/juju/jujusvg) project and is
available on [Github](https://github.com/marcoceppi/python-jujusvg).

    juju deploy --resource python-jujusvg=./python-jujusvg charm-svg

or

    juju upgrade-charm charm-svg --resource python-jujusvg=./python-jujusvg


### webapp

A tar.gz archive of the [svg.juju.solutions web application](https://github.com/marcoceppi/svg.juju.solutions)
this web application is used to interpret web requests and generate the SVG

    juju deploy --resource webapp=./app.tar.gz charm-svg

or

    juju upgrade-charm charm-svg --resource webapp=./app.tar.gz


## Scale out Usage

This charm easily scales by placing a load balancer in front of charm-svg. One
example is HAProxy

    juju deploy haproxy
    juju add-relation charm-svg haproxy
    juju unexpose charm-svg
    juju expose haproxy

However, there are several viable [loadbalancing options](https://jujucharms.com/q/?tags=cache-proxy&requires=http)

# Configuration

Those don't do anything, don't use them yet

## use-venv

## repository

## reference

# Contact Information

The author of this charm is also the author of the project!
