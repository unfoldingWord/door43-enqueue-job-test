# Do a delayed start to make sure redis is available
echo "Sleeping for 5s to wait for redis to start..."
sleep 5s

echo "Starting rq worker now..."
rq worker -c settings2

