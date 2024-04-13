# Delete stack
aws s3 rm s3://stream-raw-210570 --recursive
aws s3 rm s3://stream-redacted-210570 --recursive
aws s3 rm s3://stream-analytics-210570 --recursive
aws cloudformation delete-stack --stack-name NewsStreamStack