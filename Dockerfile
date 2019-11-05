FROM fedora:latest

RUN dnf update -y

RUN mkdir -p /testsuite && \
    chown testmaster /testsuite

USER testmaster

WORKDIR /testsuite

# Install requirements
COPY requirements.sh /testsuite/requirements.sh
CMD ["sh", "requirements.sh"]

# Copy testsuite source code
COPY 

EXPOSE 1024

# Run testsuite
CMD ["python", ""]

#RUN ./docker-install.sh 
