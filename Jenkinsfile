pipeline {
  agent {
    kubernetes {
      label 'example-kaniko-volumes'
      yaml """
kind: Pod
metadata:
  name: kaniko
spec:
  containers:
  - name: jnlp
    workingDir: /home/jenkins
  - name: kaniko
    workingDir: /home/jenkins
    image: gcr.io/kaniko-project/executor:debug
    imagePullPolicy: Always
    command:
    - /busybox/cat
    tty: true
    volumeMounts:
      - name: jenkins-docker-cfg
        mountPath: /kaniko/.docker
  volumes:
  - name: jenkins-docker-cfg
    secret:
          name: dockerhub-secret
          items:
            - key: .dockerconfigjson
              path: config.json
"""
    }
  }
  stages {
    stage('Build with Kaniko') {
      environment {
        PATH = "/busybox:/kaniko:$PATH"
      }
      steps {
        container(name: 'kaniko', shell: '/busybox/sh') {

          writeFile file: "Dockerfile", text: """
            FROM jenkins/agent
            MAINTAINER CloudBees Support Team <support@cloudbees.com>
            RUN mkdir /home/jenkins/.m2
          """

          sh '''#!/busybox/sh
            /kaniko/executor --context `pwd` --verbosity debug --destination cloudbees/jnlp-from-kaniko:latest
          '''
        }
      }
    }
  }
}