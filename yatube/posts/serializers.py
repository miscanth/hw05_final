from rest_framework import serializers

from .models import Group, Post, Tag, TagPost


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name',)
        model = Tag

class PostSerializer(serializers.ModelSerializer):
    group = serializers.SlugRelatedField(slug_field='slug',
            queryset=Group.objects.all(), required=False)
    tag = serializers.TagSerializer(many=True, required=False)

    class Meta:
        fields = ('id', 'text', 'author', 'image', 'pub_date', 'group', 'tag')
        model = Post

    def create(self, validated_data):
        if 'tag' not in self.initial_data:
            post = Post.objects.create(**validated_data)
            return post
 
        tag_data = validated_data.pop('tag')
        post = Post.objects.create(**validated_data)
        for tag in tag_data:
            current_tag, status = Tag.objects.get_or_create(
                **tag)
            TagPost.objects.create(
                tag=current_tag, post=post)
        return post