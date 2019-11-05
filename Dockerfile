FROM fedora:latest

RUN dnf update -y

# Create new user
RUN groupadd -g 1007 testmaster && \
    useradd -r -u 1007 -g testmaster testmaster
RUN mkdir -p /testsuite && \
    chown testmaster /testsuite

# Install requirements
COPY setup-env.sh /testsuite/setup-env.sh
CMD ["bash", "setup-env.sh"]


# Switch to user
################
USER testmaster

WORKDIR /testsuite

# Install requirements
COPY setup-usr-env.sh.sh /testsuite/setup-usr-env.sh
CMD ["bash", "setup-usr-env.sh"]

# Copy testsuite source code
#COPY 

EXPOSE 1024

# Run testsuite
#CMD ["python", ""]

#RUN ./docker-install.sh 
