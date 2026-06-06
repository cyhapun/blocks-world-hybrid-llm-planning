(define (problem bw_easy_003)
  (:domain blocks-world)

  (:objects
    a b c - block
  )

  (:init
    (on_table a)
    (on b c)
    (clear a)
    (clear c)
    (handempty)
  )

  (:goal
    (on c a)
  )
)
