#!groovy
/**
 * -*- indent-tabs-mode: nil -*-
 * -*- tab-width: 4 -*-
 * Work in tandem with tests/docker/Dockerfile & Co to run a full CI run in
 * Jenkins.
*/
node {
    stage("Checkout") {
        checkout scm
    }
    withEnv(["PYTHON_VERSION=2"]) {
        load 'Jenkinsfile-common'
    }
}
